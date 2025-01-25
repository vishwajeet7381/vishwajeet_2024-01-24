CREATE TABLE IF NOT EXISTS store_status (
    store_id UUID,
    timestamp_utc TIMESTAMP(6),
    status VARCHAR(10) CHECK (status IN ('active', 'inactive')),
    PRIMARY KEY (store_id, timestamp_utc)
);
CREATE TABLE IF NOT EXISTS business_hours (
    store_id UUID,
    day_of_week INTEGER CHECK (
        day_of_week BETWEEN 0 AND 6
    ),
    start_time_local TIME(6) NOT NULL,
    end_time_local TIME(6) NOT NULL,
    PRIMARY KEY (store_id, day_of_week)
);
CREATE TABLE IF NOT EXISTS store_timezone (
    store_id UUID PRIMARY KEY,
    timezone_str VARCHAR(50) DEFAULT 'America/Chicago' NOT NULL
);
CREATE TABLE IF NOT EXISTS reports (
    report_id UUID PRIMARY KEY,
    status VARCHAR(20) DEFAULT 'running' CHECK (
        status IN ('running', 'completed', 'failed')
    ),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS report_data (
    report_id UUID,
    store_id UUID,
    uptime_last_hour DOUBLE PRECISION NOT NULL,
    uptime_last_day DOUBLE PRECISION NOT NULL,
    uptime_last_week DOUBLE PRECISION NOT NULL,
    downtime_last_hour DOUBLE PRECISION NOT NULL,
    downtime_last_day DOUBLE PRECISION NOT NULL,
    downtime_last_week DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (report_id, store_id)
);