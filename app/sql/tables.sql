CREATE TABLE IF NOT EXISTS store_status (
    store_id uuid,
    status varchar(10) CHECK (status IN ('active', 'inactive')),
    timestamp_utc timestamp,
    PRIMARY KEY (store_id, timestamp_utc)
);
CREATE TABLE IF NOT EXISTS business_hours (
    store_id uuid,
    day_of_week integer CHECK (
        day_of_week BETWEEN 0 AND 6
    ),
    start_time_local time NOT NULL,
    end_time_local time NOT NULL,
    PRIMARY KEY (store_id, day_of_week)
);
CREATE TABLE IF NOT EXISTS store_timezone (
    store_id uuid PRIMARY KEY,
    timezone_str varchar(50) DEFAULT 'America/Chicago'
);
CREATE TABLE IF NOT EXISTS reports (
    report_id uuid PRIMARY KEY,
    status varchar(20) DEFAULT 'running',
    started_at timestamp DEFAULT current_timestamp,
    completed_at timestamp
);
CREATE TABLE IF NOT EXISTS report_data (
    report_id uuid,
    store_id uuid,
    uptime_last_hour integer,
    uptime_last_day integer,
    uptime_last_week integer,
    downtime_last_hour integer,
    downtime_last_day integer,
    downtime_last_week integer,
    PRIMARY KEY (report_id, store_id)
);