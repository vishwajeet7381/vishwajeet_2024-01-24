import psycopg
from psycopg.rows import dict_row

from app.config import Config


class DatabaseManager:
    def __init__(
        self,
        host: str | None = None,
        port: str | None = None,
        dbname: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ):
        self._conn_info: dict = {
            "host": host or Config.postgresql_host,
            "port": port or Config.postgresql_port,
            "dbname": dbname or Config.postgresql_dbname,
            "user": user or Config.postgresql_user,
            "password": password or Config.postgresql_password,
        }

        self._conn: psycopg.Connection
        self._cur: psycopg.Cursor

    def connect(self) -> psycopg.Cursor:
        conn_info_dict = {
            key: value for key, value in self._conn_info.items() if value is not None
        }

        conn_info_str = psycopg.conninfo.make_conninfo(**conn_info_dict)

        self._conn = psycopg.connect(conn_info_str, row_factory=dict_row)
        self._cur = self._conn.cursor()

        return self._cur

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._cur.close()
        self._conn.close()

    def __enter__(self) -> psycopg.Cursor:
        return self.connect()

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()
