"""Разбор событий. Независим от Kafka/PostgreSQL, чтобы проверять локально."""

import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone


@dataclass(frozen=True)
class Event:
    event_id: str
    sensor_id: str
    event_time: datetime
    temperature_c: float

    @property
    def event_day(self):
        return self.event_time.date()


def parse_event(payload: bytes) -> Event:
    try:
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("message must be JSON object")

        event_id = data["event_id"]
        sensor_id = data["sensor_id"]
        if not isinstance(event_id, str) or not 1 <= len(event_id) <= 120:
            raise ValueError("event_id must be a nonempty string")
        if not isinstance(sensor_id, str) or not re.fullmatch(r"[a-z0-9_-]{1,32}", sensor_id):
            raise ValueError("invalid sensor_id")

        raw_time = data["event_time"]
        if not isinstance(raw_time, str):
            raise ValueError("event_time must be an ISO timestamp")
        event_time = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
        if event_time.tzinfo is None:
            raise ValueError("event_time must include timezone")
        event_time = event_time.astimezone(timezone.utc)

        raw_temp = data["temperature_c"]
        if isinstance(raw_temp, bool) or not isinstance(raw_temp, (int, float)):
            raise ValueError("temperature_c must be numeric")
        temp = float(raw_temp)
        if not math.isfinite(temp) or not -80 <= temp <= 150:
            raise ValueError("temperature_c outside permitted range")

        return Event(event_id, sensor_id, event_time, temp)
    except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError, OverflowError) as exc:
        raise ValueError(f"invalid event: {exc}") from exc


def sample_events(now=None):
    """Детерминированная выборка с задержками, дублями и out-of-order."""
    now = now or datetime.now(timezone.utc)
    old_day = now.date() - timedelta(days=3)
    middle_day = now.date() - timedelta(days=2)
    yesterday = now.date() - timedelta(days=1)

    def at(day, hour, minute):
        return datetime.combine(day, time(hour, minute), tzinfo=timezone.utc)

    rows = [
        ("01", "sensor_msk_1", at(old_day, 8, 0), 21.50),
        ("02", "sensor_msk_1", at(old_day, 8, 10), 22.00),
        ("03", "sensor_msk_2", at(old_day, 8, 15), 18.00),
        ("04", "sensor_msk_2", at(old_day, 23, 59), 18.40),
        ("05", "sensor_msk_1", at(middle_day, 0, 1), 21.10),
        ("06", "sensor_msk_1", at(middle_day, 9, 20), 20.90),
        ("07", "sensor_msk_2", at(middle_day, 13, 0), 19.00),
        ("08", "sensor_msk_2", at(yesterday, 8, 0), 17.80),
        ("09", "sensor_msk_1", at(yesterday, 9, 0), 21.30),
    ]
    events = [
        {"event_id": f"iot-{when.date()}-{number}", "sensor_id": sensor,
         "event_time": when.isoformat(), "temperature_c": temp}
        for number, sensor, when, temp in rows
    ]
    order = [0, 4, 7, 1, 2, 6, 8, 3, 5, 1, 3, 6]
    return [events[index] for index in order]
