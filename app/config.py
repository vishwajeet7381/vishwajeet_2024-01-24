import os


class Config:
    postgresql_host = os.environ.get("SM_POSTGRESQL_HOST")
    postgresql_port = os.environ.get("SM_POSTGRESQL_PORT")
    postgresql_dbname = os.environ.get("SM_POSTGRESQL_DBNAME") or "postgres"
    postgresql_user = os.environ.get("SM_POSTGRESQL_USER") or "postgres"
    postgresql_password = os.environ.get("SM_POSTGRESQL_PASSWORD")

    create_tables = False
    load_data = False
