import csv
from pathlib import Path

from app.database import DatabaseManager


class DatabaseSetup:
    current_file_path: Path = Path(__file__)

    @classmethod
    def create_tables(cls):
        sql_file_path = cls.current_file_path.parents[1] / Path("sql/tables.sql")

        with sql_file_path.open("rt") as file_handler:
            queries = file_handler.read()

            with DatabaseManager() as db_cur:
                db_cur.execute(queries)

    @classmethod
    def load_data(
        cls, dataset_dir_path: str | Path | None = None, *file_names: str | Path
    ):
        dataset_dir_path_ = (
            Path(dataset_dir_path)
            if dataset_dir_path
            else cls.current_file_path.parents[2] / "dataset"
        )

        store_status_file_path = dataset_dir_path_ / (
            Path(file_names[0]) if len(file_names) > 0 else "store_status.csv"
        )
        business_hours_file_path = dataset_dir_path_ / (
            Path(file_names[1]) if len(file_names) > 1 else "store_business_hours.csv"
        )
        store_timezone_file_path = dataset_dir_path_ / (
            Path(file_names[2]) if len(file_names) > 2 else "store_timezone.csv"
        )

        with DatabaseManager() as db_cur:
            with store_status_file_path.open("rt", newline="") as file_handler:
                csv_reader = csv.reader(file_handler)

                next(csv_reader)

                with db_cur.copy(
                    """
                    COPY store_status (store_id, status, timestamp_utc)
                    FROM STDIN;"""
                ) as copy:
                    for record in csv_reader:
                        copy.write_row(record)

            with business_hours_file_path.open("rt", newline="") as file_handler:
                csv_reader = csv.reader(file_handler)

                next(csv_reader)

                db_cur.execute(
                    """
                    CREATE TEMP TABLE temp_business_hours
                    (LIKE business_hours INCLUDING DEFAULTS)"""
                )

                with db_cur.copy(
                    """
                    COPY temp_business_hours (
                        store_id,
                        day_of_week,
                        start_time_local,
                        end_time_local
                    )
                    FROM STDIN;"""
                ) as copy:
                    for record in csv_reader:
                        copy.write_row(record)

                db_cur.execute(
                    """
                    INSERT INTO business_hours
                    SELECT *
                    FROM temp_business_hours ON CONFLICT (store_id, day_of_week) DO NOTHING;"""
                )

            with store_timezone_file_path.open("rt", newline="") as file_handler:
                csv_reader = csv.reader(file_handler)

                next(csv_reader)

                db_cur.executemany(
                    """
                    INSERT INTO store_timezone (store_id, timezone_str)
                    VALUES (%s, %s) ON CONFLICT (store_id) DO
                    UPDATE
                    SET timezone_str = EXCLUDED.timezone_str;""",
                    tuple(csv_reader),
                )
