import contextlib

from fastapi import FastAPI

from app.utils.setup_database import SetupDatabase


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    SetupDatabase.create_tables()
    SetupDatabase.load_data()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def root():
    return {"message": "Hello, World!"}
