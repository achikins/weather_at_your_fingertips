from typing import Any
from sqlalchemy.orm import Session
from services.station_service import get_all_stations, get_first_station_id, station_exists
from services.weather_service import get_available_years, get_monthly_weather
from services.summary_service import calculate_annual_summary

def _normalize_monthly_for_summary(monthly: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for row in monthly:
        min_h = row.get("avg_min_humidity_pct")
        max_h = row.get("avg_max_humidity_pct")

        humidity = None
        if min_h is not None and max_h is not None:
            humidity = round((min_h + max_h) / 2, 2)

        wind_ms = row.get("avg_wind_speed_ms")
        wind_kmh = None if wind_ms is None else round(wind_ms * 3.6, 2)

        normalized.append({
            "tempMin": row.get("avg_min_temp_c"),
            "tempMax": row.get("avg_max_temp_c"),
            "tempAvg": row.get("avg_temp_c"),
            "rainfall": row.get("total_rain_mm"),
            "humidity": humidity,
            "windSpeed": wind_kmh,
        })

    return normalized


def build_dashboard_payload(
    db: Session,
    station_id: int | None = None,
    year: int | None = None,
    include_stations: bool = True,
) -> dict[str, Any]:
    stations: list[dict[str, Any]] | None = None
    if include_stations:
        stations = get_all_stations(db)
        if not stations:
            return {
                "stations": [],
                "selected_station_id": None,
                "available_years": [],
                "selected_year": None,
                "monthly": [],
            }

    if station_id is None:
        # Use station_id 1 as the default if it exists.
        if station_exists(db, 1):
            selected_station_id = 1
        else:
            selected_station_id = get_first_station_id(db)
            if selected_station_id is None:
                return {
                    "stations": [] if include_stations else None,
                    "selected_station_id": None,
                    "available_years": [],
                    "selected_year": None,
                    "monthly": [],
                }
    else:
        if not station_exists(db, station_id):
            raise ValueError("Station not found")
        selected_station_id = station_id

    available_years = get_available_years(db, selected_station_id)

    selected_year = year
    if selected_year is None and available_years:
        selected_year = available_years[0]

    monthly = get_monthly_weather(db, selected_station_id, year=selected_year)

    payload: dict[str, Any] = {
        "selected_station_id": selected_station_id,
        "available_years": available_years,
        "selected_year": selected_year,
        "monthly": monthly,
        "summary": calculate_annual_summary(_normalize_monthly_for_summary(monthly)),
    }

    if include_stations:
        payload["stations"] = stations if stations is not None else []

    return payload
