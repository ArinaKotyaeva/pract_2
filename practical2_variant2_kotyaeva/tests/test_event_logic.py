"""Запуск: PYTHONPATH=app python -m unittest discover -s tests -v"""

import json
import unittest
from datetime import date

from event_logic import parse_event, sample_events


class EventLogicTests(unittest.TestCase):
    def test_normalizes_time_to_utc(self):
        event = parse_event(json.dumps({
            "event_id": "id", "sensor_id": "sensor_1",
            "event_time": "2026-01-02T01:30:00+03:00", "temperature_c": 20.5,
        }).encode())
        self.assertEqual(event.event_day, date(2026, 1, 1))

    def test_fails_without_timezone(self):
        payload = b'{"event_id":"1","sensor_id":"sensor_1","event_time":"2026-01-01T01:00:00","temperature_c":22}'
        with self.assertRaises(ValueError):
            parse_event(payload)

    def test_rejects_nan_and_boolean(self):
        for value in (float("nan"), True):
            with self.subTest(value=value):
                payload = json.dumps({
                    "event_id": "x", "sensor_id": "sensor_1",
                    "event_time": "2026-01-01T00:00:00Z", "temperature_c": value,
                }).encode()
                with self.assertRaises(ValueError):
                    parse_event(payload)

    def test_demo_has_three_duplicates(self):
        events = sample_events()
        self.assertEqual(len(events), 12)
        self.assertEqual(len({event["event_id"] for event in events}), 9)

    def test_event_time_is_not_arrival_order(self):
        events = sample_events()
        times = [parse_event(json.dumps(event).encode()).event_time for event in events]
        self.assertNotEqual(times, sorted(times))


if __name__ == "__main__":
    unittest.main()
