from typing import Any
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import extract, func
from sqlalchemy.orm import Session
from models import DailyWeather, Forecast, MonthlyAggregate, Station
from services.number_utils import ms_to_kmh, round_one_decimal, to_float
from services.station_service import get_station_years, station_exists

CITY_TO_STATION = {
    "sydney": 423,
    "melbourne": 277,
    "brisbane": 44,
    "perth": 365,
    "adelaide": 1,
    "darwin": 122,
    "hobart": 189,
    "cairns": 57,
    "goldcoast": 166,
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

def _average_pair(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return (a + b) / 2

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

def _serialize_forecast_weather(row: Forecast) -> dict[str, Any]:
    pred_max_temp_c = to_float(row.pred_max_temp_c)
    pred_min_temp_c = to_float(row.pred_min_temp_c)
    pred_max_humidity_pct = to_float(row.pred_max_humidity_pct)
    pred_min_humidity_pct = to_float(row.pred_min_humidity_pct)
    pred_rain_mm = to_float(row.pred_rain_mm)
    wind_speed_ms = to_float(row.pred_wind_speed_ms)
    wind_speed_kmh = ms_to_kmh(wind_speed_ms)
    avg_temp_c = _average_pair(pred_max_temp_c, pred_min_temp_c)
    avg_humidity_pct = _average_pair(pred_max_humidity_pct, pred_min_humidity_pct)
    return {
        "forecast_date": row.forecast_date.isoformat(),
        "horizon_days": row.horizon_days,
        "pred_max_temp_c": round_one_decimal(pred_max_temp_c),
        "pred_min_temp_c": round_one_decimal(pred_min_temp_c),
        "pred_avg_temp_c": round_one_decimal(avg_temp_c),
        "pred_rain_mm": round_one_decimal(pred_rain_mm),
        "pred_max_humidity_pct": round_one_decimal(pred_max_humidity_pct),
        "pred_min_humidity_pct": round_one_decimal(pred_min_humidity_pct),
        "pred_avg_humidity_pct": round_one_decimal(avg_humidity_pct),
        # Keep ms field for backwards compatibility; add km/h for frontend display consistency.
        "pred_wind_speed_ms": round_one_decimal(wind_speed_ms),
        "pred_wind_speed_kmh": round_one_decimal(wind_speed_kmh),
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

def get_station_next_7_day_forecast(db: Session, station_id: int) -> dict[str, Any]:
    today = datetime.now(ZoneInfo("Australia/Melbourne")).date()

    latest_generated_at = (
        db.query(func.max(Forecast.generated_at))
        .filter(Forecast.station_id == station_id)
        .scalar()
    )

    if latest_generated_at is None:
        return {
            "cityId": city_id_for_station_id(station_id),
            "station_id": station_id,
            "generated_at": None,
            "forecast": [],
        }

    end_date = today + timedelta(days=6)
    rows = (
        db.query(Forecast)
        .filter(
            Forecast.station_id == station_id,
            Forecast.generated_at == latest_generated_at,
            Forecast.forecast_date >= today,
            Forecast.forecast_date <= end_date,
        )
        .order_by(Forecast.forecast_date.asc(), Forecast.horizon_days.asc())
        .all()
    )

    return {
        "cityId": city_id_for_station_id(station_id),
        "station_id": station_id,
        "generated_at": latest_generated_at.isoformat(),
        "forecast": [_serialize_forecast_weather(row) for row in rows],
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

def resolve_city_stations(
    db: Session,
    city_id: str | None = None,
) -> list[tuple[str, Station]]:
    if city_id is not None:
        normalized_city_id = city_id.lower().strip()
        station_id = resolve_station_for_city(db, normalized_city_id)
        station = db.query(Station).filter(Station.station_id == station_id).first()
        if station is None:
            return []
        return [(normalized_city_id, station)]

    mapped_station_ids = list(CITY_TO_STATION.values())
    stations = db.query(Station).filter(Station.station_id.in_(mapped_station_ids)).all()
    station_by_id = {station.station_id: station for station in stations}

    city_stations: list[tuple[str, Station]] = []
    for mapped_city_id in sorted(CITY_TO_STATION.keys()):
        station = station_by_id.get(CITY_TO_STATION[mapped_city_id])
        if station is not None:
            city_stations.append((mapped_city_id, station))
    return city_stations

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
        wind_kmh = None if wind_ms is None else round(ms_to_kmh(wind_ms), 2)
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
    avg_temp = _average_pair(max_temp, min_temp)

    min_h = today_forecast.get("pred_min_humidity_pct")
    max_h = today_forecast.get("pred_max_humidity_pct")
    humidity = _average_pair(min_h, max_h)

    wind_ms = today_forecast.get("pred_wind_speed_ms")
    wind_kmh = ms_to_kmh(wind_ms)

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

def _aggregate_monthly(monthly: list[dict[str, Any]]) -> dict[str, Any]:
    """Reduce a list of normalised monthly rows to a single annual summary."""
    def avg(field: str) -> float | None:
        values = [row[field] for row in monthly if row.get(field) is not None]
        if not values:
            return None
        return round(sum(values) / len(values), 1)

    return {
        "tempAvg": avg("tempAvg"),
        "rainfall": avg("rainfall"),
        "humidity": avg("humidity"),
        "windSpeed": avg("windSpeed"),
    }

def get_cities_summary(
    db: Session,
    year: int | None = None,
) -> list[dict[str, Any]]:
    """Return aggregated annual summary for every supported city."""
    summary = []
    for city_id in sorted(CITY_TO_STATION.keys()):
        try:
            payload = get_city_weather(db, city_id, year=year)
        except ValueError:
            continue
        aggregates = _aggregate_monthly(payload["monthly"])
        summary.append({
            "cityId": payload["cityId"],
            "station_id": payload["station_id"],
            "year": payload["selected_year"],
            **aggregates,
        })
    return summary

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
