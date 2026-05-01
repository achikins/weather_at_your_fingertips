from decimal import Decimal
from typing import Any
from sqlalchemy.orm import Session
from models import DailyWeather, MonthlyAggregate

def _to_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)

def _serialize_daily_weather(row: DailyWeather) -> dict[str, Any]:
    return {
        "obs_date": row.obs_date.isoformat(),
        "rain_mm": _to_float(row.rain_mm),
        "max_temp_c": _to_float(row.max_temp_c),
        "min_temp_c": _to_float(row.min_temp_c),
        "max_humidity_pct": _to_float(row.max_humidity_pct),
        "min_humidity_pct": _to_float(row.min_humidity_pct),
        "avg_wind_speed_mps": _to_float(row.avg_wind_speed_mps),
    }

def _serialize_monthly_weather(row: MonthlyAggregate) -> dict[str, Any]:
    avg_temp = None
    if row.avg_max_temp_c is not None and row.avg_min_temp_c is not None:
        avg_temp = float((row.avg_max_temp_c + row.avg_min_temp_c) / 2)

    return {
        "year": row.station_year,
        "month": row.station_month,
        "avg_max_temp_c": _to_float(row.avg_max_temp_c),
        "avg_min_temp_c": _to_float(row.avg_min_temp_c),
        "avg_temp_c": avg_temp,
        "total_rain_mm": _to_float(row.total_rain_mm),
        "avg_min_humidity_pct": _to_float(row.avg_min_humidity_pct),
        "avg_max_humidity_pct": _to_float(row.avg_max_humidity_pct),
        "avg_wind_speed_ms": _to_float(row.avg_wind_speed_ms),
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

def get_available_years(db: Session, station_id: int) -> list[int]:
    rows = (
        db.query(MonthlyAggregate.station_year)
        .filter(MonthlyAggregate.station_id == station_id)
        .distinct()
        .order_by(MonthlyAggregate.station_year.desc())
        .all()
    )

    return [row[0] for row in rows]
