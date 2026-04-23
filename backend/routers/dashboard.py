from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db
from services.dashboard_service import build_dashboard_payload

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/")
def get_dashboard_data(
    station_id: int | None = None,
    year: int | None = None,
    include_stations: bool = True,
    db: Session = Depends(get_db),
):
    try:
        return build_dashboard_payload(
            db,
            station_id=station_id,
            year=year,
            include_stations=include_stations,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
