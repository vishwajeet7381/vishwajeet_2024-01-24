import os


class Config:
    POSTGRESQL_HOST = os.environ.get("SM_POSTGRESQL_HOST")
    POSTGRESQL_PORT = os.environ.get("SM_POSTGRESQL_PORT")
    POSTGRESQL_DBNAME = os.environ.get("SM_POSTGRESQL_DBNAME") or "postgres"
    POSTGRESQL_USER = os.environ.get("SM_POSTGRESQL_USER") or "postgres"
    POSTGRESQL_PASSWORD = os.environ.get("SM_POSTGRESQL_PASSWORD")
