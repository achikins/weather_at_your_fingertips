from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from database import engine
from jobs.generate_alerts import run as run_alert_generation
from jobs.generate_openweather_alerts import run as run_openweather_alert_generation
from models import Base
from routers import alerts, weather, stations
from services.alert_schedule import (
    FORECAST_ALERT_JOB_MINUTE_UTC,
    OPENWEATHER_ALERT_JOB_HOUR_UTC,
    OPENWEATHER_ALERT_JOB_MINUTE_UTC,
)
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Weather at Your Fingertips API",
    description="API documentation for weather data, weather stations, and alert services.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    )
scheduler = BackgroundScheduler(timezone="UTC")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://weather-at-your-fingertips.arjaywonx.workers.dev",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# create tables
Base.metadata.create_all(bind=engine)

app.include_router(stations.router, prefix="/api")
app.include_router(weather.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")

@app.on_event("startup")
def start_scheduler() -> None:
    scheduler.add_job(
        run_alert_generation,
        trigger="cron",
        minute=FORECAST_ALERT_JOB_MINUTE_UTC,
        id="generate_alerts_job",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_job(
        run_openweather_alert_generation,
        trigger="cron",
        hour=OPENWEATHER_ALERT_JOB_HOUR_UTC,
        minute=OPENWEATHER_ALERT_JOB_MINUTE_UTC,
        id="generate_openweather_alerts_job",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    scheduler.start()

@app.on_event("shutdown")
def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)

@app.get("/")
def root():
    return {"message": "API running"}
