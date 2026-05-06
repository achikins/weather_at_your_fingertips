from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from dependencies import get_db
from services.weather_service import (
    get_historical_weather,
    get_station_weather,
    get_city_weather,
    get_supported_cities,
    resolve_station_from_params,
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

@router.get("/weather/current")
def get_current_weather(
    city_id: str | None = None,
    station_id: str | None = None,
    db: Session = Depends(get_db),
):
    try:
        resolved_city_id, resolved_station_id = resolve_station_from_params(
            db,
            city_id=city_id,
            station_id=station_id,
        )
        payload = get_station_weather(db, resolved_station_id)
        payload["cityId"] = resolved_city_id or payload["cityId"]
        return {
            "cityId": payload["cityId"],
            "station_id": payload["station_id"],
            "current": payload["current"],
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.get("/weather/monthly")
def get_monthly_weather_query(
    city_id: str | None = None,
    station_id: str | None = None,
    year: int | None = None,
    db: Session = Depends(get_db),
):
    try:
        resolved_city_id, resolved_station_id = resolve_station_from_params(
            db,
            city_id=city_id,
            station_id=station_id,
        )
        payload = get_station_weather(db, resolved_station_id, year=year)
        payload["cityId"] = resolved_city_id or payload["cityId"]
        return {
            "cityId": payload["cityId"],
            "station_id": payload["station_id"],
            "available_years": payload["available_years"],
            "selected_year": payload["selected_year"],
            "monthly": payload["monthly"],
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.get("/weather/historical")
def get_historical_weather_query(
    city_id: str | None = None,
    station_id: str | None = None,
    year: int | None = None,
    month: int | None = Query(default=None, ge=1, le=12),
    day: int | None = Query(default=None, ge=1, le=31),
    db: Session = Depends(get_db),
):
    try:
        resolved_city_id, resolved_station_id = resolve_station_from_params(
            db,
            city_id=city_id,
            station_id=station_id,
        )
        historical = get_historical_weather(
            db,
            station_id=resolved_station_id,
            year=year,
            month=month,
            day=day,
        )
        return {
            "cityId": resolved_city_id,
            "station_id": resolved_station_id,
            "filters": {
                "year": year,
                "month": month,
                "day": day,
            },
            "historical": historical,
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
