from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dependencies import get_db
from services.station_service import (
    get_all_stations as get_all_stations_service,
)

router = APIRouter(prefix="/stations", tags=["Stations"])

@router.get("/")
def get_all_stations(db: Session = Depends(get_db)):
    return get_all_stations_service(db)
