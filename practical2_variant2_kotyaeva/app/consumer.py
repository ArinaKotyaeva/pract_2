"""Kafka -> PostgreSQL: at-least-once delivery, idempotent database effect."""

import logging
import os
import time

import psycopg
from confluent_kafka import Consumer, KafkaException

from event_logic import parse_event


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://iot:iot_demo_password@localhost:15432/iot")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
TOPIC = os.getenv("KAFKA_TOPIC", "iot.events")


def write_message(connection, message):
    """Атомарно пишем сырое событие и увеличиваем счетчик только при первом INSERT."""
    payload = message.value() or b""
    try:
        event = parse_event(payload)
    except ValueError as exc:
        with connection.transaction():
            connection.execute(
                """INSERT INTO rejected_events
                   (topic, partition_id, kafka_offset, raw_payload, error_reason)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (topic, partition_id, kafka_offset) DO NOTHING""",
                (message.topic(), message.partition(), message.offset(),
                 payload.decode("utf-8", errors="replace"), str(exc)),
            )
        logging.warning("Event routed to rejected_events: %s", exc)
        return "rejected"

    with connection.transaction():
        inserted = connection.execute(
            """INSERT INTO raw_events
               (event_id, sensor_id, event_time, temperature_c, is_late)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (event_id) DO NOTHING RETURNING event_id""",
            (event.event_id, event.sensor_id, event.event_time,
             event.temperature_c,
             (event.event_time.timestamp() < time.time() - 48 * 3600)),
        ).fetchone()
        if inserted is not None:
            connection.execute(
                """INSERT INTO live_daily_metrics
                   (event_day, sensor_id, events_count, temperature_sum)
                   VALUES (%s, %s, 1, %s)
                   ON CONFLICT (event_day, sensor_id) DO UPDATE SET
                       events_count = live_daily_metrics.events_count + 1,
                       temperature_sum = live_daily_metrics.temperature_sum + EXCLUDED.temperature_sum,
                       updated_at = now()""",
                (event.event_day, event.sensor_id, event.temperature_c),
            )
    return "inserted" if inserted is not None else "duplicate"


def main():
    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": "iot-postgres-materializer-v1",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
        "enable.auto.offset.store": False,
    })
    consumer.subscribe([TOPIC])
    connection = None
    try:
        while True:
            if connection is None or connection.closed:
                try:
                    connection = psycopg.connect(DATABASE_URL, autocommit=True)
                except psycopg.OperationalError:
                    logging.exception("PostgreSQL unavailable; retrying")
                    time.sleep(3)
                    continue
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())
            try:
                result = write_message(connection, msg)
                # Сначала COMMIT в БД, только затем offset в Kafka.
                # Повтор при сбое между этими шагами безопасен благодаря PRIMARY KEY.
                consumer.commit(message=msg, asynchronous=False)
                logging.info("%s offset=%s event=%s", result, msg.offset(), msg.key())
            except psycopg.Error:
                logging.exception("Database transaction failed; will reprocess")
                connection.close()
                time.sleep(2)
                # Без подтверждения offset обработка начнется заново после рестарта.
                raise
    finally:
        if connection is not None:
            connection.close()
        consumer.close()


if __name__ == "__main__":
    main()
