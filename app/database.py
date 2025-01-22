import psycopg

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
            "host": host or Config.POSTGRESQL_HOST,
            "port": port or Config.POSTGRESQL_PORT,
            "dbname": dbname or Config.POSTGRESQL_DBNAME,
            "user": user or Config.POSTGRESQL_USER,
            "password": password or Config.POSTGRESQL_PASSWORD,
        }

        self._conn: psycopg.Connection
        self._cur: psycopg.Cursor

    def connect(self) -> psycopg.Cursor:
        conn_info_dict = {
            key: value for key, value in self._conn_info.items() if value is not None
        }

        conn_info_str = psycopg.conninfo.make_conninfo(**conn_info_dict)

        self._conn = psycopg.connect(conn_info_str)
        self._cur = self.conn.cursor()

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
