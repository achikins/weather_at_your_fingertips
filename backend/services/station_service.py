from sqlalchemy.orm import Session
from models import MonthlyAggregate, Station
from services.number_utils import to_float

def _serialize_station(station: Station) -> dict[str, Any]:
    return {
        "station_id": station.station_id,
        "station_name": station.station_name,
        "state": station.state,
        "latitude": to_float(station.latitude),
        "longitude": to_float(station.longitude),
        "elevation_m": to_float(station.elevation_m),
        "start_date": station.start_date.isoformat() if station.start_date else None,
        "end_date": station.end_date.isoformat() if station.end_date else None,
        "coverage_pct": to_float(station.coverage_pct),
    }

def get_all_stations(db: Session) -> list[dict[str, Any]]:
    stations = db.query(Station).order_by(Station.station_name.asc()).all()
    return [_serialize_station(station) for station in stations]

def station_exists(db: Session, station_id: int) -> bool:
    return db.query(Station.station_id).filter(Station.station_id == station_id).first() is not None

def get_station_years(db: Session, station_id: int) -> list[int]:
    rows = (
        db.query(MonthlyAggregate.station_year)
        .filter(MonthlyAggregate.station_id == station_id)
        .distinct()
        .order_by(MonthlyAggregate.station_year.desc())
        .all()
    )

    return [row[0] for row in rows]
