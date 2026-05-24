from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from dependencies import get_db
from services.weather_service import (
    get_station_next_7_day_forecast,
    get_historical_weather,
    get_station_weather,
    get_city_weather,
    get_cities_summary,
    get_supported_cities,
    resolve_station_from_params,
)

router = APIRouter(tags=["Weather"])

@router.get(
    "/cities",
    summary="Get supported cities",
    description="Returns the list of cities supported by the weather dashboard.",
    )
def get_cities():
    return {"cities": get_supported_cities()}

@router.get(
    "/weather/cities/summary",
    summary="Get aggregated weather summary for all supported cities",
    description=(
        "Returns annual averages (temperature, rainfall, humidity, wind speed) "
        "for every supported city in one batch call. Used by the map view to "
        "colour station markers."
    ),
)
def get_cities_summary_endpoint(
    year: int | None = None,
    db: Session = Depends(get_db),
):
    return {"summary": get_cities_summary(db, year=year)}

@router.get(
    "/weather/city/{city_id}",
    summary="Get city weather",
    description="Returns weather data for a selected city, with an optional year filter.",
    )
def get_weather_for_city(
    city_id: str,
    year: int | None = None,
    db: Session = Depends(get_db),
):
    try:
        return get_city_weather(db, city_id, year=year)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.get(
    "/weather/forecast",
    summary="Get 7-day forecast by city or station",
    description="Returns forecasted weather data for the next 7 days using either a city ID or station ID.",
    )
def get_forecast_weather_query(
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
        payload = get_station_next_7_day_forecast(db, resolved_station_id)
        payload["cityId"] = resolved_city_id or payload["cityId"]
        return {
            "cityId": payload["cityId"],
            "station_id": payload["station_id"],
            "generated_at": payload["generated_at"],
            "forecast": payload["forecast"],
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.get(
    "/weather/city/{city_id}/monthly",
    summary="Get monthly city weather",
    description="Returns monthly weather data for a selected city and optional year.",
    )
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

@router.get(
    "/weather/city/{city_id}/current",
    summary="Get current city weather",
    description="Returns current weather data for a selected city and optional year.",
    )
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

@router.get(
    "/weather/current",
    summary="Get current weather by city or station",
    description="Returns current weather data using either a city ID or station ID.",
    )
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

@router.get(
    "/weather/monthly",
    summary="Get monthly weather by city or station",
    description="Returns monthly weather data using either a city ID or station ID, with an optional year filter.",
    )
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

@router.get(
    "/weather/historical",
    summary="Get historical weather",
    description="Returns historical weather records using city ID or station ID, with optional year, month, and day filters.",
    )
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
