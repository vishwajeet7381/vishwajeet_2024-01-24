import csv
from datetime import datetime
from pathlib import Path

from app.database import DatabaseManager


class DatabaseSetup:
    current_file: Path = Path(__file__)

    @classmethod
    def create_tables(cls):
        sql_file = cls.current_file.parents[1] / Path("sql/tables.sql")

        with sql_file.open("rt") as file_handler:
            queries = file_handler.read()

            with DatabaseManager() as db_cur:
                db_cur.execute(queries)

    @classmethod
    def load_data(cls, dataset_dir: str | Path | None = None, *file_names: str | Path):
        dataset_dir_ = (
            Path(dataset_dir)
            if dataset_dir
            else cls.current_file.parents[2] / "dataset"
        )

        store_status_file = dataset_dir_ / (
            Path(file_names[0]) if len(file_names) > 0 else "store_status.csv"
        )
        business_hours_file = dataset_dir_ / (
            Path(file_names[1]) if len(file_names) > 1 else "store_business_hours.csv"
        )
        store_timezone_file = dataset_dir_ / (
            Path(file_names[2]) if len(file_names) > 2 else "store_timezone.csv"
        )

        with DatabaseManager() as db_cur:
            with store_status_file.open("rt", newline="") as file_handler:
                csv_reader = csv.reader(file_handler)

                next(csv_reader)

                for record in csv_reader:
                    record[2] = datetime.strptime(record[2], "%Y-%m-%d %H:%M:%S.%f %Z")

                    db_cur.execute(
                        """
                        INSERT INTO store_status (store_id, status, timestamp_utc)
                        VALUES (%s, %s, %s) ON CONFLICT (store_id, timestamp_utc) DO NOTHING;""",
                        record,
                    )

            with business_hours_file.open("rt", newline="") as file_handler:
                csv_reader = csv.reader(file_handler)

                next(csv_reader)

                for record in csv_reader:
                    record[2] = datetime.strptime(record[2], "%H:%M:%S").time()
                    record[3] = datetime.strptime(record[3], "%H:%M:%S").time()

                    db_cur.execute(
                        """
                        INSERT INTO business_hours (
                                store_id,
                                day_of_week,
                                start_time_local,
                                end_time_local
                            )
                        VALUES (%s, %s, %s, %s) ON CONFLICT (store_id, day_of_week) DO NOTHING;""",
                        record,
                    )

            with store_timezone_file.open("rt", newline="") as file_handler:
                csv_reader = csv.reader(file_handler)

                next(csv_reader)

                db_cur.executemany(
                    """
                    INSERT INTO store_timezone (store_id, timezone_str)
                    VALUES (%s, %s) ON CONFLICT (store_id) DO NOTHING;""",
                    list(csv_reader),
                )
