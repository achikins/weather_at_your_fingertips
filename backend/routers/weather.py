from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db
from services.station_service import station_exists
from services.weather_service import (
    get_available_years,
    get_daily_weather as get_daily_weather_service,
    get_monthly_weather as get_monthly_weather_service,
)

router = APIRouter(prefix="/weather", tags=["Weather"])

@router.get("/{station_id}/daily")
def get_daily_weather(station_id: int, db: Session = Depends(get_db)):
    if not station_exists(db, station_id):
        raise HTTPException(status_code=404, detail="Station not found")

    return {
        "station_id": station_id,
        "daily": get_daily_weather_service(db, station_id),
    }

@router.get("/{station_id}/years")
def get_weather_years(station_id: int, db: Session = Depends(get_db)):
    if not station_exists(db, station_id):
        raise HTTPException(status_code=404, detail="Station not found")

    return {"station_id": station_id, "years": get_available_years(db, station_id)}

@router.get("/{station_id}/monthly")
def get_monthly_weather(
    station_id: int,
    year: int | None = None,
    db: Session = Depends(get_db),
):
    if not station_exists(db, station_id):
        raise HTTPException(status_code=404, detail="Station not found")

    return {
        "station_id": station_id,
        "year": year,
        "monthly": get_monthly_weather_service(db, station_id, year=year),
    }
