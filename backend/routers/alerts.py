from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db
from services.alert_service import get_alerts

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get(
    "/",
    summary="Get all alerts",
    description="Returns all weather alerts stored in the system.",
    )
def get_all_alerts(db: Session = Depends(get_db)):
    return {"alerts": get_alerts(db)}

@router.get(
    "/{city_id}",
    summary="Get alerts for a city",
    description="Returns weather alerts for a selected city.",
    )
def get_city_alerts(city_id: str, db: Session = Depends(get_db)):
    try:
        return {"cityId": city_id.lower().strip(), "alerts": get_alerts(db, city_id=city_id)}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc