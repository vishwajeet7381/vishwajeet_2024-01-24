import csv
import uuid
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from psycopg.rows import tuple_row

from app.database import DatabaseManager


class ReportGenerator:
    def __init__(
        self, report_id: str | None = None, current_time: datetime | None = None
    ):
        self._report_id: str | None = report_id
        self._current_time: datetime | None = current_time

    def generate_report_id(self) -> str:
        self._report_id = str(uuid.uuid4())

        with DatabaseManager() as db_cur:
            db_cur.execute(
                """
                INSERT INTO reports (report_id)
                VALUES (%s);""",
                (self._report_id,),
            )

        return self._report_id

    def generate_report(self):
        if self._current_time is None:
            self._calculate_current_time()

        stores = self._get_all_stores()

        for store in stores:
            store_id = store["store_id"]

            try:
                store_timezone = self._get_store_timezone(store_id)

                business_hours = self._get_business_hours(store_id)

                report_data = self._calculate_uptime_downtime(
                    store_id, store_timezone, business_hours
                )

                self._store_report_data(store_id, report_data)
            except Exception as e:
                print(f"Error processing store {store_id}: {str(e)}")
                continue

        self._update_report_status("completed")

    def check_status(self) -> str:
        with DatabaseManager() as db_cur:
            db_cur.execute(
                "SELECT status FROM reports WHERE report_id = %s;", (self._report_id,)
            )
            result = db_cur.fetchone()
            return result["status"].lower() if result else "running"

    def get_report_path(self) -> Path:
        report_dir = Path(__file__).parents[1] / "reports"
        report_dir.mkdir(exist_ok=True)
        report_file = report_dir / f"{self._report_id}.csv"

        if report_file.exists():
            return report_file

        with DatabaseManager() as db_cur:
            db_cur.row_factory = tuple_row

            db_cur.execute(
                """
                SELECT 
                    store_id, 
                    uptime_last_hour,
                    uptime_last_day,
                    uptime_last_week,
                    downtime_last_hour,
                    downtime_last_day,
                    downtime_last_week
                FROM report_data 
                WHERE report_id = %s;""",
                (self._report_id,),
            )
            data = db_cur.fetchall()

        fieldnames = [
            "store_id",
            "uptime_last_hour",
            "uptime_last_day",
            "uptime_last_week",
            "downtime_last_hour",
            "downtime_last_day",
            "downtime_last_week",
        ]

        with open(report_file, "wt", newline="") as file_handler:
            writer = csv.writer(file_handler)

            writer.writerow(fieldnames)

            writer.writerows(data)

        return report_file

    def _calculate_current_time(self):
        with DatabaseManager() as db_cur:
            db_cur.execute(
                """
                SELECT MAX(timestamp_utc) as max_time
                FROM store_status;"""
            )

            result = db_cur.fetchone()

            self._current_time = result["max_time"].astimezone(ZoneInfo("UTC"))

    def _get_all_stores(self) -> list[dict[str, str]]:
        with DatabaseManager() as db_cur:
            db_cur.execute("SELECT DISTINCT store_id FROM store_status;")

            return db_cur.fetchall()

    def _get_store_timezone(self, store_id: str) -> ZoneInfo:
        with DatabaseManager() as db_cur:
            db_cur.execute(
                "SELECT timezone_str FROM store_timezone WHERE store_id = %s;",
                (store_id,),
            )

            result = db_cur.fetchone()

            return ZoneInfo(result["timezone_str"])

    def _get_business_hours(self, store_id: str) -> dict[int, list]:
        with DatabaseManager() as db_cur:
            db_cur.execute(
                """
                SELECT day_of_week,
                    start_time_local,
                    end_time_local
                FROM business_hours
                WHERE store_id = %s;""",
                (store_id,),
            )

            business_hours = {}

            for row in db_cur:
                business_hours[row["day_of_week"]] = [
                    row["start_time_local"],
                    row["end_time_local"],
                ]

        return business_hours

    def _calculate_uptime_downtime(
        self, store_id: str, store_timezone: ZoneInfo, business_hours: dict[int, list]
    ) -> dict[str, float]:
        report_intervals = {
            "last_hour": (self._current_time - timedelta(hours=1), self._current_time),
            "last_day": (self._current_time - timedelta(days=1), self._current_time),
            "last_week": (self._current_time - timedelta(weeks=1), self._current_time),
        }

        results = {
            "uptime_last_hour": 0,
            "uptime_last_day": 0,
            "uptime_last_week": 0,
            "downtime_last_hour": 0,
            "downtime_last_day": 0,
            "downtime_last_week": 0,
        }

        for period, (start, end) in report_intervals.items():
            active_time, inactive_time = self._calculate_for_interval(
                store_id, start, end, business_hours, store_timezone
            )

            if period == "last_hour":
                results["uptime_last_hour"] = active_time
                results["downtime_last_hour"] = inactive_time
            elif period == "last_day":
                results["uptime_last_day"] = active_time / 60
                results["downtime_last_day"] = inactive_time / 60
            elif period == "last_week":
                results["uptime_last_week"] = active_time / 60
                results["downtime_last_week"] = inactive_time / 60

        return results

    def _calculate_for_interval(
        self,
        store_id: str,
        interval_start: datetime,
        interval_end: datetime,
        business_hours: dict[int, list],
        store_timezone: ZoneInfo,
    ) -> tuple[float, float]:
        # Convert business hours to UTC for the given interval
        business_periods = self._get_business_periods(
            interval_start, interval_end, business_hours, store_timezone
        )

        total_active = 0
        total_inactive = 0

        for period_start, period_end in business_periods:
            # Get activity data for this business period
            with DatabaseManager() as db_cur:
                db_cur.execute(
                    """
                    SELECT timestamp_utc, status 
                    FROM store_status 
                    WHERE store_id = %s 
                    AND timestamp_utc >= %s 
                    AND timestamp_utc <= %s 
                    ORDER BY timestamp_utc;""",
                    (
                        store_id,
                        period_start.replace(tzinfo=None),
                        period_end.replace(tzinfo=None),
                    ),
                )

                observations = [
                    {
                        "timestamp_utc": obs["timestamp_utc"].astimezone(
                            ZoneInfo("UTC")
                        ),
                        "status": obs["status"],
                    }
                    for obs in db_cur
                ]

            # Calculate active/inactive time using observations
            active, inactive = self._interpolate_observations(
                period_start, period_end, observations
            )

            total_active += active
            total_inactive += inactive

        return total_active, total_inactive

    def _get_business_periods(
        self,
        interval_start: datetime,
        interval_end: datetime,
        business_hours: dict[int, list],
        store_timezone: ZoneInfo,
    ) -> list[list[datetime]]:
        periods = []
        current_day = interval_start.date()

        while current_day <= interval_end.date():
            day_of_week = current_day.weekday()
            start_time, end_time = business_hours.get(
                day_of_week, (time(0, 0), time(23, 59, 59))
            )

            # Create timezone-aware datetimes with explicit fold
            local_start = datetime.combine(
                current_day, start_time, tzinfo=store_timezone
            ).replace(fold=0)

            local_end = datetime.combine(
                current_day, end_time, tzinfo=store_timezone
            ).replace(fold=0)

            # Convert to UTC
            utc_start = local_start.astimezone(ZoneInfo("UTC"))
            utc_end = local_end.astimezone(ZoneInfo("UTC"))

            # Clip to report interval
            period_start = max(utc_start, interval_start)
            period_end = min(utc_end, interval_end)

            if period_start < period_end:
                periods.append([period_start, period_end])

            current_day += timedelta(days=1)

        return periods

    def _interpolate_observations(
        self,
        start: datetime,
        end: datetime,
        observations: list[dict[str, str | datetime]],
    ) -> tuple[float, float]:
        if not observations:
            # Assume active if no data
            return (end - start).total_seconds() / 60, 0

        # Add interval boundaries as virtual observations
        sorted_obs = [
            {"timestamp_utc": start, "status": None},
            *observations,
            {"timestamp_utc": end, "status": None},
        ]

        active = 0
        inactive = 0

        for i in range(1, len(sorted_obs)):
            prev = sorted_obs[i - 1]
            curr = sorted_obs[i]

            time_diff = (
                curr["timestamp_utc"] - prev["timestamp_utc"]
            ).total_seconds() / 60

            if time_diff <= 0:
                continue

            # Use previous status for the interval
            status = prev["status"] if prev["status"] else curr["status"]

            if status == "active":
                active += time_diff
            else:
                inactive += time_diff

        return active, inactive

    def _store_report_data(self, store_id: str, data: dict[str, float]):
        with DatabaseManager() as db_cur:
            db_cur.execute(
                """
                INSERT INTO report_data (
                        report_id,
                        store_id,
                        uptime_last_hour,
                        uptime_last_day,
                        uptime_last_week,
                        downtime_last_hour,
                        downtime_last_day,
                        downtime_last_week
                    )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);""",
                (
                    self._report_id,
                    store_id,
                    data["uptime_last_hour"],
                    data["uptime_last_day"],
                    data["uptime_last_week"],
                    data["downtime_last_hour"],
                    data["downtime_last_day"],
                    data["downtime_last_week"],
                ),
            )

    def _update_report_status(self, status: str):
        with DatabaseManager() as db_cur:
            db_cur.execute(
                """
                UPDATE reports 
                SET status = %s, completed_at = NOW() 
                WHERE report_id = %s""",
                (
                    status,
                    self._report_id,
                ),
            )
