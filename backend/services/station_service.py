from decimal import Decimal
from typing import Any
from sqlalchemy.orm import Session
from models import MonthlyAggregate, Station

def _to_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)

def _serialize_station(station: Station) -> dict[str, Any]:
    return {
        "station_id": station.station_id,
        "station_name": station.station_name,
        "state": station.state,
        "latitude": _to_float(station.latitude),
        "longitude": _to_float(station.longitude),
        "elevation_m": _to_float(station.elevation_m),
        "start_date": station.start_date.isoformat() if station.start_date else None,
        "end_date": station.end_date.isoformat() if station.end_date else None,
        "coverage_pct": _to_float(station.coverage_pct),
    }

def get_all_stations(db: Session) -> list[dict[str, Any]]:
    stations = db.query(Station).order_by(Station.station_name.asc()).all()
    return [_serialize_station(station) for station in stations]

def station_exists(db: Session, station_id: int) -> bool:
    return db.query(Station.station_id).filter(Station.station_id == station_id).first() is not None

def get_first_station_id(db: Session) -> int | None:
    row = db.query(Station.station_id).order_by(Station.station_id.asc()).first()
    if row is None:
        return None
    return row[0]

def get_station_years(db: Session, station_id: int) -> list[int]:
    rows = (
        db.query(MonthlyAggregate.station_year)
        .filter(MonthlyAggregate.station_id == station_id)
        .distinct()
        .order_by(MonthlyAggregate.station_year.desc())
        .all()
    )

    return [row[0] for row in rows]
