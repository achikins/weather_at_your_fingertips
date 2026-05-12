from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db
from services.station_service import (
    get_all_stations as get_all_stations_service,
    get_station_by_id as get_station_by_id_service,
)

router = APIRouter(prefix="/stations", tags=["Stations"])

@router.get(
    "/",
    summary="Get all weather stations",
    description="Returns a list of all available weather stations.",
    )
def get_all_stations(db: Session = Depends(get_db)):
    return get_all_stations_service(db)

@router.get(
    "/{station_id}",
    summary="Get station by ID",
    description="Returns detailed information for a specific weather station.",
    )
def get_station_by_id(station_id: int, db: Session = Depends(get_db)):
    station = get_station_by_id_service(db, station_id)
    if station is None:
        raise HTTPException(status_code=404, detail=f"Station {station_id} not found")
    return station
