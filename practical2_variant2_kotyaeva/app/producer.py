"""Демо: девять событий, три дубликата, нарушенный порядок и поздние записи."""

import json
import logging
import os

from confluent_kafka import Producer
from event_logic import sample_events


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
TOPIC = os.getenv("KAFKA_TOPIC", "iot.events")
BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")


def main():
    producer = Producer({
        "bootstrap.servers": BOOTSTRAP,
        "acks": "all",
        "enable.idempotence": True,
        "message.timeout.ms": 30000,
    })
    failures = []

    def delivered(err, msg):
        if err:
            failures.append(str(err))
        else:
            logging.info("delivered event_id=%s partition=%s offset=%s",
                         msg.key().decode(), msg.partition(), msg.offset())

    events = sample_events()
    for event in events:
        producer.produce(TOPIC, key=event["event_id"],
                         value=json.dumps(event).encode("utf-8"), callback=delivered)
        producer.poll(0)
    remaining = producer.flush(40)
    if failures or remaining:
        raise RuntimeError(f"Not all messages confirmed: errors={failures}, remaining={remaining}")
    logging.info("sent=%s; unique=9; intentional_duplicates=3", len(events))


if __name__ == "__main__":
    main()
