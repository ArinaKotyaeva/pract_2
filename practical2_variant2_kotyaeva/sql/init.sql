-- Все event_time храним с часовым поясом; отчётный день считается по UTC.
CREATE TABLE IF NOT EXISTS raw_events (
    event_id TEXT PRIMARY KEY,
    sensor_id TEXT NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    temperature_c NUMERIC(8, 2) NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_late BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_raw_events_day
    ON raw_events ((event_time AT TIME ZONE 'UTC')::date);

CREATE TABLE IF NOT EXISTS live_daily_metrics (
    event_day DATE NOT NULL,
    sensor_id TEXT NOT NULL,
    events_count BIGINT NOT NULL CHECK (events_count >= 0),
    temperature_sum NUMERIC(16, 2) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (event_day, sensor_id)
);

CREATE TABLE IF NOT EXISTS batch_daily_reports (
    event_day DATE NOT NULL,
    sensor_id TEXT NOT NULL,
    events_count BIGINT NOT NULL,
    avg_temperature_c NUMERIC(8, 2) NOT NULL,
    refreshed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (event_day, sensor_id)
);

-- Даже некорректное сообщение сохраняется, а не теряется без следа.
CREATE TABLE IF NOT EXISTS rejected_events (
    topic TEXT NOT NULL,
    partition_id INTEGER NOT NULL,
    kafka_offset BIGINT NOT NULL,
    raw_payload TEXT NOT NULL,
    error_reason TEXT NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (topic, partition_id, kafka_offset)
);
