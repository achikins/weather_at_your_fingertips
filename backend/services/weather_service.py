from typing import Any
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import extract
from sqlalchemy.orm import Session
from models import DailyWeather, Forecast, MonthlyAggregate
from services.number_utils import round_one_decimal, to_float
from services.station_service import get_station_years, station_exists

CITY_TO_STATION = {
    "sydney": 64,
    "melbourne": 277,
    "brisbane": 44,
    "perth": 365,
    "adelaide": 1,
    "darwin": 121,
    "hobart": 187,
    "cairns": 57,
    "goldcoast": 165,
    "canberra": 63,
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

def _serialize_daily_weather(row: DailyWeather) -> dict[str, Any]:
    return {
        "obs_date": row.obs_date.isoformat(),
        "rain_mm": to_float(row.rain_mm),
        "max_temp_c": to_float(row.max_temp_c),
        "min_temp_c": to_float(row.min_temp_c),
        "max_humidity_pct": to_float(row.max_humidity_pct),
        "min_humidity_pct": to_float(row.min_humidity_pct),
        "avg_wind_speed_mps": to_float(row.avg_wind_speed_mps),
    }

def _serialize_monthly_weather(row: MonthlyAggregate) -> dict[str, Any]:
    avg_temp = None
    if row.avg_max_temp_c is not None and row.avg_min_temp_c is not None:
        avg_temp = float((row.avg_max_temp_c + row.avg_min_temp_c) / 2)

    return {
        "year": row.station_year,
        "month": row.station_month,
        "avg_max_temp_c": to_float(row.avg_max_temp_c),
        "avg_min_temp_c": to_float(row.avg_min_temp_c),
        "avg_temp_c": avg_temp,
        "total_rain_mm": to_float(row.total_rain_mm),
        "avg_min_humidity_pct": to_float(row.avg_min_humidity_pct),
        "avg_max_humidity_pct": to_float(row.avg_max_humidity_pct),
        "avg_wind_speed_ms": to_float(row.avg_wind_speed_ms),
        "days_recorded": row.days_recorded,
    }

def get_daily_weather(db: Session, station_id: int) -> list[dict[str, Any]]:
    rows = (
        db.query(DailyWeather)
        .filter(DailyWeather.station_id == station_id)
        .order_by(DailyWeather.obs_date.asc())
        .all()
    )

    return [_serialize_daily_weather(row) for row in rows]

def get_today_forecast_weather(db: Session, station_id: int) -> dict[str, Any] | None:
    today = datetime.now(ZoneInfo("Australia/Melbourne")).date()
    row = (
        db.query(Forecast)
        .filter(
            Forecast.station_id == station_id,
            Forecast.forecast_date == today,
        )
        .order_by(Forecast.generated_at.desc(), Forecast.id.desc())
        .first()
    )
    if row is None:
        return None

    return {
        "forecast_date": row.forecast_date.isoformat(),
        "pred_max_temp_c": to_float(row.pred_max_temp_c),
        "pred_min_temp_c": to_float(row.pred_min_temp_c),
        "pred_rain_mm": to_float(row.pred_rain_mm),
        "pred_max_humidity_pct": to_float(row.pred_max_humidity_pct),
        "pred_min_humidity_pct": to_float(row.pred_min_humidity_pct),
        "pred_wind_speed_ms": to_float(row.pred_wind_speed_ms),
    }

def get_monthly_weather(
    db: Session,
    station_id: int,
    year: int | None = None,
) -> list[dict[str, Any]]:
    query = db.query(MonthlyAggregate).filter(MonthlyAggregate.station_id == station_id)

    if year is not None:
        query = query.filter(MonthlyAggregate.station_year == year)

    rows = query.order_by(MonthlyAggregate.station_year.asc(), MonthlyAggregate.station_month.asc()).all()

    return [_serialize_monthly_weather(row) for row in rows]

def get_supported_cities() -> list[str]:
    return sorted(CITY_TO_STATION.keys())

def city_id_for_station_id(station_id: int) -> str | None:
    for city_id, mapped_station_id in CITY_TO_STATION.items():
        if mapped_station_id == station_id:
            return city_id
    return None

def resolve_station_for_city(db: Session, city_id: str) -> int:
    normalized = city_id.lower().strip()
    station_id = CITY_TO_STATION.get(normalized)
    if station_id is None:
        raise ValueError(f"Unsupported city: {city_id}")
    if not station_exists(db, station_id):
        raise ValueError(f"Mapped station not found for city: {city_id}")
    return station_id

def normalize_monthly(monthly: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for row in monthly:
        month_num = row.get("month")
        year_num = row.get("year")
        min_h = row.get("avg_min_humidity_pct")
        max_h = row.get("avg_max_humidity_pct")

        humidity = None
        if min_h is not None and max_h is not None:
            humidity = round((min_h + max_h) / 2, 2)

        wind_ms = row.get("avg_wind_speed_ms")
        wind_kmh = None if wind_ms is None else round(wind_ms * 3.6, 2)
        date = None
        if year_num is not None and month_num is not None:
            date = f"{year_num}-{month_num:02d}-01"

        normalized.append(
            {
                "year": year_num,
                "month": MONTH_NAMES.get(month_num, str(month_num)),
                "monthIndex": (month_num - 1) if isinstance(month_num, int) else None,
                "date": date,
                "tempMin": round_one_decimal(row.get("avg_min_temp_c")),
                "tempMax": round_one_decimal(row.get("avg_max_temp_c")),
                "tempAvg": round_one_decimal(row.get("avg_temp_c")),
                "rainfall": round_one_decimal(row.get("total_rain_mm")),
                "humidity": round_one_decimal(humidity),
                "windSpeed": round_one_decimal(wind_kmh),
            }
        )
    return normalized

def derive_current_from_forecast(today_forecast: dict[str, Any] | None) -> dict[str, Any] | None:
    if today_forecast is None:
        return None

    max_temp = today_forecast.get("pred_max_temp_c")
    min_temp = today_forecast.get("pred_min_temp_c")
    avg_temp = None
    if max_temp is not None and min_temp is not None:
        avg_temp = (max_temp + min_temp) / 2

    min_h = today_forecast.get("pred_min_humidity_pct")
    max_h = today_forecast.get("pred_max_humidity_pct")
    humidity = None
    if min_h is not None and max_h is not None:
        humidity = (min_h + max_h) / 2

    wind_ms = today_forecast.get("pred_wind_speed_ms")
    wind_kmh = None if wind_ms is None else wind_ms * 3.6

    return {
        "obsDate": today_forecast.get("forecast_date"),
        "temp": round_one_decimal(avg_temp),
        "tempMin": round_one_decimal(min_temp),
        "tempMax": round_one_decimal(max_temp),
        "humidity": round_one_decimal(humidity),
        "windSpeed": round_one_decimal(wind_kmh),
        "rainfall": round_one_decimal(today_forecast.get("pred_rain_mm")),
    }

def _build_station_weather_payload(
    db: Session,
    station_id: int,
    year: int | None = None,
) -> dict[str, Any]:
    available_years = get_station_years(db, station_id)
    selected_year = year
    if selected_year is None and available_years:
        selected_year = available_years[0]
    if selected_year is not None and selected_year not in available_years:
        raise ValueError(f"Year {selected_year} does not exist for station: {station_id}")

    monthly_raw = get_monthly_weather(db, station_id, year=selected_year)
    monthly = normalize_monthly(monthly_raw)
    today_forecast = get_today_forecast_weather(db, station_id)
    current = derive_current_from_forecast(today_forecast)

    return {
        "cityId": city_id_for_station_id(station_id),
        "station_id": station_id,
        "available_years": available_years,
        "selected_year": selected_year,
        "monthly": monthly,
        "current": current,
    }

def get_city_weather(
    db: Session,
    city_id: str,
    year: int | None = None,
) -> dict[str, Any]:
    normalized_city = city_id.lower().strip()
    station_id = resolve_station_for_city(db, normalized_city)
    payload = _build_station_weather_payload(db, station_id, year=year)
    payload["cityId"] = normalized_city
    return payload

def resolve_station_from_params(
    db: Session,
    city_id: str | None = None,
    station_id: str | int | None = None,
) -> tuple[str | None, int]:
    if city_id:
        normalized_city = city_id.lower().strip()
        return normalized_city, resolve_station_for_city(db, normalized_city)

    if station_id is None:
        raise ValueError("Provide either city_id or station_id")

    if isinstance(station_id, int):
        if not station_exists(db, station_id):
            raise ValueError(f"Station not found: {station_id}")
        return city_id_for_station_id(station_id), station_id

    normalized_station = station_id.lower().strip()
    if normalized_station.isdigit():
        numeric_station_id = int(normalized_station)
        if not station_exists(db, numeric_station_id):
            raise ValueError(f"Station not found: {station_id}")
        return city_id_for_station_id(numeric_station_id), numeric_station_id

    return normalized_station, resolve_station_for_city(db, normalized_station)

def get_station_weather(
    db: Session,
    station_id: int,
    year: int | None = None,
) -> dict[str, Any]:
    return _build_station_weather_payload(db, station_id, year=year)

def get_historical_weather(
    db: Session,
    station_id: int,
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
) -> list[dict[str, Any]]:
    query = db.query(DailyWeather).filter(DailyWeather.station_id == station_id)

    if year is not None:
        query = query.filter(extract("year", DailyWeather.obs_date) == year)
    if month is not None:
        query = query.filter(extract("month", DailyWeather.obs_date) == month)
    if day is not None:
        query = query.filter(extract("day", DailyWeather.obs_date) == day)

    rows = query.order_by(DailyWeather.obs_date.asc()).all()
    return [_serialize_daily_weather(row) for row in rows]
