from typing import Any
from sqlalchemy.orm import Session
from services.station_service import station_exists
from services.weather_service import get_available_years, get_monthly_weather
from services.summary_service import calculate_annual_summary

CITY_TO_STATION = {
    "sydney": 63,
    "melbourne": 274,
    "brisbane": 43,
    "perth": 363,
    "adelaide": 0,
    "darwin": 120,
    "hobart": 185,
    "cairns": 57,
    "goldcoast": 163,
    "canberra": 62,
}

MONTH_NAMES = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}

def _normalize_monthly_for_compare(monthly: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for row in monthly:
        avg_humidity = None
        min_h = row.get("avg_min_humidity_pct")
        max_h = row.get("avg_max_humidity_pct")
        if min_h is not None and max_h is not None:
            avg_humidity = round((min_h + max_h) / 2, 2)

        wind_ms = row.get("avg_wind_speed_ms")
        wind_kmh = None if wind_ms is None else round(wind_ms * 3.6, 2)

        normalized.append(
            {
                "month": MONTH_NAMES.get(row["month"], str(row["month"])),
                "monthIndex": row["month"] - 1,
                "tempMin": row.get("avg_min_temp_c"),
                "tempMax": row.get("avg_max_temp_c"),
                "tempAvg": row.get("avg_temp_c"),
                "rainfall": row.get("total_rain_mm"),
                "humidity": avg_humidity,
                "windSpeed": wind_kmh,
            }
        )

    return normalized

def _resolve_station_for_city(db: Session, city_id: str) -> int:
    station_id = CITY_TO_STATION.get(city_id.lower().strip())
    if station_id is None:
        raise ValueError(f"Unsupported city: {city_id}")

    if not station_exists(db, station_id):
        raise ValueError(f"Mapped station not found for city: {city_id}")

    return station_id

def build_compare_payload(
    db: Session,
    city1: str,
    city2: str,
    year: int | None = None,
) -> dict[str, Any]:
    city1_id = city1.lower().strip()
    city2_id = city2.lower().strip()

    if city1_id == city2_id:
        raise ValueError("city1 and city2 must be different")

    station1 = _resolve_station_for_city(db, city1_id)
    station2 = _resolve_station_for_city(db, city2_id)

    years1 = get_available_years(db, station1)
    years2 = get_available_years(db, station2)
    common_years = sorted(set(years1).intersection(years2), reverse=True)

    selected_year = year
    if selected_year is None and common_years:
        selected_year = common_years[0]

    if selected_year is not None and selected_year not in common_years:
        raise ValueError(f"Year {selected_year} does not exist for both cities")

    monthly1 = []
    monthly2 = []
    if selected_year is not None:
        monthly1 = _normalize_monthly_for_compare(get_monthly_weather(db, station1, year=selected_year))
        monthly2 = _normalize_monthly_for_compare(get_monthly_weather(db, station2, year=selected_year))

    return {
        "available_years": common_years,
        "selected_year": selected_year,
        "city1": {
            "city_id": city1_id,
            "station_id": station1,
            "available_years": years1,
            "monthly": monthly1,
            "summary": calculate_annual_summary(monthly1),
        },
        "city2": {
            "city_id": city2_id,
            "station_id": station2,
            "available_years": years2,
            "monthly": monthly2,
            "summary": calculate_annual_summary(monthly2),
        },
    }
