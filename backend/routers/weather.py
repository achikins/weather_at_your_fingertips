from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db
from services.weather_service import (
    get_city_weather,
    get_supported_cities,
)

router = APIRouter(tags=["Weather"])

@router.get("/cities")
def get_cities():
    return {"cities": get_supported_cities()}

@router.get("/weather/city/{city_id}")
def get_weather_for_city(
    city_id: str,
    year: int | None = None,
    db: Session = Depends(get_db),
):
    try:
        return get_city_weather(db, city_id, year=year)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.get("/weather/city/{city_id}/monthly")
def get_city_monthly_weather(
    city_id: str,
    year: int | None = None,
    db: Session = Depends(get_db),
):
    try:
        payload = get_city_weather(db, city_id, year=year)
        return {
            "cityId": payload["cityId"],
            "station_id": payload["station_id"],
            "available_years": payload["available_years"],
            "selected_year": payload["selected_year"],
            "monthly": payload["monthly"],
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.get("/weather/city/{city_id}/current")
def get_city_current_weather(
    city_id: str,
    year: int | None = None,
    db: Session = Depends(get_db),
):
    try:
        payload = get_city_weather(db, city_id, year=year)
        return {
            "cityId": payload["cityId"],
            "station_id": payload["station_id"],
            "selected_year": payload["selected_year"],
            "current": payload["current"],
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
