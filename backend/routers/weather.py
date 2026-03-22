from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import DailyWeather, Station, MonthlyAggregate
from dependencies import get_db

router = APIRouter(prefix="/weather", tags=["Weather"])

@router.get("/{station_id}/daily")
def get_daily_weather(station_id: int, db: Session = Depends(get_db)):
    station = db.query(Station).filter(Station.station_id == station_id).first()

    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    return db.query(DailyWeather).filter(
        DailyWeather.station_id == station_id
    ).all()

@router.get("/{station_id}/monthly")
def get_monthly_weather(station_id: int, db: Session = Depends(get_db)):
    station = db.query(Station).filter(Station.station_id == station_id).first()

    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    return db.query(MonthlyAggregate).filter(
        MonthlyAggregate.station_id == station_id
    ).order_by(
        MonthlyAggregate.station_year.desc(),
        MonthlyAggregate.station_month.desc()
    ).all()