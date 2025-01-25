import contextlib

from fastapi import BackgroundTasks, FastAPI
from fastapi.responses import FileResponse

from app.config import Config
from app.report_generator import ReportGenerator
from app.utils.database_setup import DatabaseSetup


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    if Config.create_tables:
        DatabaseSetup.create_tables()

    if Config.load_data:
        DatabaseSetup.load_data()

    yield


app = FastAPI(
    title="Store Monitoring System",
    summary="This application exposes API to create report on stores uptime and downtime for different time intervals",
    lifespan=lifespan,
)


@app.post("/trigger_report", tags=["report"])
async def trigger_report(background_tasks: BackgroundTasks) -> dict:
    report_generator_ = ReportGenerator()

    report_id = report_generator_.generate_report_id()

    background_tasks.add_task(report_generator_.generate_report)

    return {"report_id": report_id}


@app.get("/get_report/{report_id}", tags=["report"])
async def get_report(report_id: str) -> FileResponse:
    report_generator_ = ReportGenerator(report_id)

    report_status = report_generator_.check_status()

    if report_status == "running":
        return {"status": "Running"}

    report_file = report_generator_.get_report_path()

    return FileResponse(
        report_file,
        headers={"Report-Status": "Completed"},
        media_type="text/csv",
        filename=f"report_{report_file.name}",
    )
