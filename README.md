# Store Monitoring System

This application provides APIs to generate reports on the uptime and downtime of restaurants during their business hours. It processes data from CSV files, stores it in a PostgreSQL database, and generates reports based on the provided data.

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Setup Instructions](#setup-instructions)
4. [API Documentation](#api-documentation)
5. [Database Schema](#database-schema)
6. [Report Generation Logic](#report-generation-logic)
7. [Configuration](#configuration)
8. [Running the Application](#running-the-application)
9. [Testing](#testing)
10. [Improvement Ideas](#improvement-ideas)

## Features

- **Data Ingestion**: Loads CSV data into a PostgreSQL database.
- **Report Generation**: Generates uptime/downtime reports for stores.
- **Background Processing**: Handles report generation asynchronously.
- **Time Zone Handling**: Supports local time zones for business hours.
- **CSV Export**: Exports reports in CSV format for easy consumption.

## Tech Stack

- **Backend**: Python and FastAPI
- **DBMS**: PostgreSQL
- **Project Management (including dependency and environment)**: uv

## Setup Instructions

### Prerequisites

- Python 3.12+
- PostgreSQL
- uv

### Steps

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/vishwajeet7381/vishwajeet_2024-01-24.git
   cd store-monitoring-system
   ```

2. **Set Up PostgreSQL**:

   - Install PostgreSQL if not available
   - Update the database credentials in `app/config.py` or set the following environment variables as appropriate:
     ```bash
     export SM_POSTGRESQL_HOST=value
     export SM_POSTGRESQL_PORT=value
     export SM_POSTGRESQL_DBNAME=value
     export SM_POSTGRESQL_USER=value
     export SM_POSTGRESQL_PASSWORD=value
     ```

3. **Dataset**:
   - Place your CSV files (`store_status.csv`, `store_business_hours.csv`, `store_timezone.csv`) in the `dataset` directory.

## API Documentation

### 1. Trigger Report Generation

- **Endpoint**: `POST /trigger_report`
- **Description**: Initiates report generation.
- **Response**:
  ```json
  {
    "report_id": "uuid-string"
  }
  ```

### 2. Get Report Status or Download

- **Endpoint**: `GET /get_report/{report_id}`
- **Description**: Returns the status of the report or the CSV file if completed.
- **Response**:
  - If report is still running:
    ```json
    {
      "status": "Running"
    }
    ```
  - If report is completed:
    - Returns a CSV file with the following fields:
      ```csv
      store_id,uptime_last_hour,uptime_last_day,uptime_last_week,downtime_last_hour,downtime_last_day,downtime_last_week
      ```

## Database Schema

- [Database schema](app/sql/tables.sql)

## Report Generation Logic

1. **Uptime and Downtime Calculation**

   The system calculates uptime and downtime for three intervals:

   1. **Last Hour** (in minutes)
   2. **Last Day** (in hours)
   3. **Last Week** (in hours)

   **Steps**:

   1. **Determine Report Intervals**:
      - The latest timestamp in `store_status.csv` is considered the "current time."
      - Intervals are calculated as:
        - **Last Hour**: `[current_time - 1 hour, current_time]`
        - **Last Day**: `[current_time - 24 hours, current_time]`
        - **Last Week**: `[current_time - 7 days, current_time]`
   2. **Filter Activity Polls**:
      - Only polls within the business hours (converted to UTC) are considered.
      - Polls outside business hours are ignored.
   3. **Interpolate Uptime/Downtime**:
      - For each interval, the system divides the time into segments based on activity polls.
      - If no polls exist during a segment:
        - Assume the store is **inactive** (downtime).
      - If polls exist:
        - Use the status of the nearest previous poll to determine uptime/downtime for the segment.
   4. **Extrapolate to Full Interval**:
      - The uptime/downtime for each segment is extrapolated to the entire interval.

2. **Output Schema**

   The final report contains the following fields for each store:

   - `store_id`: Unique identifier for the store.
   - `uptime_last_hour`: Uptime in the last hour (in minutes).
   - `uptime_last_day`: Uptime in the last day (in hours).
   - `uptime_last_week`: Uptime in the last week (in hours).
   - `downtime_last_hour`: Downtime in the last hour (in minutes).
   - `downtime_last_day`: Downtime in the last day (in hours).
   - `downtime_last_week`: Downtime in the last week (in hours).

3. **Assumptions**

   1. **Poll Frequency**:
      - Polls occur roughly every hour, but intervals may vary.
      - If no polls exist during business hours, the store is assumed to be **inactive** for the entire interval.
   2. **Business Hours**:
      - If no business hours are provided, the store is assumed to be open 24/7.
   3. **Time Zones**:
      - If no timezone is provided, the default is `America/Chicago`.
   4. **Report Intervals**:
      - Intervals are calculated relative to the latest timestamp in `store_status.csv`.

## Configuration

Update `app/config.py` to customize the following:

- Database connection details.
- Enable/disable table creation (`create_tables`).
- Enable/disable data loading (`load_data`).
- Enable/disable report file deletion after download (`delete_report`).

## Running the Application

Start the FastAPI server in development mode:

```bash
uv run fastapi dev [app.main:app]
```

Access the API documentation at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing

Either use the automated interactive documentation UI accessed via `/docs` and `/redoc` paths or use the `curl` command:

1. **Trigger a Report**:

   ```bash
   curl -X POST http://localhost:8000/trigger_report
   ```

2. **Check Report Status**:

   ```bash
   curl http://localhost:8000/get_report/{report_id}
   ```

3. **Download Report**:
   - If the report is completed, the CSV file will be downloaded automatically.

## Improvement Ideas

1. **Documentation**:
   - Add more comments and docstrings.
2. **Performance**:
   - Keep track of data updates and avoid processing when result is already available for the current dataset.
3. **Error Handling & Logging**:
   - Implement structured error handling.
   - Add logging for critical operations, errors, and system events.
4. **Security**:
   - Add user authentication and role-based access control.
   - Implement rate limiting.
5. **Deployment**:
   - Containerize the application using Docker.
6. **Testing**:
   - Add unit tests for critical components.
7. **User Experience**:
   - Add progress tracking and email notifications for report completion.
