"""Пересчет суточных отчетов из единственного дедуплицированного raw-слоя."""

import logging
import os

import psycopg


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://iot:iot_demo_password@localhost:15432/iot")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main():
    with psycopg.connect(DATABASE_URL) as connection:
        with connection.transaction():
            # Полный пересчет устраняет ошибки оперативных счетчиков и учитывает
            # даже очень поздние события, которые пришли после прошлого batch.
            connection.execute("TRUNCATE batch_daily_reports")
            connection.execute(
                """INSERT INTO batch_daily_reports
                   (event_day, sensor_id, events_count, avg_temperature_c, refreshed_at)
                   SELECT (event_time AT TIME ZONE 'UTC')::date,
                          sensor_id, count(*), round(avg(temperature_c), 2), now()
                   FROM raw_events
                   GROUP BY (event_time AT TIME ZONE 'UTC')::date, sensor_id"""
            )
        for row in connection.execute(
            "SELECT event_day, sensor_id, events_count, avg_temperature_c "
            "FROM batch_daily_reports ORDER BY event_day, sensor_id"
        ):
            logging.info("day=%s sensor=%s count=%s avg=%s", *row)


if __name__ == "__main__":
    main()
