from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from dependencies import get_db
from services.alert_service import get_alerts

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get(
    "/",
    summary="Get all alerts",
    description="Returns all weather alerts stored in the system.",
    )
def get_all_alerts(
    include_inactive: bool = Query(
        default=False,
        description="If true, include inactive/expired alerts as well.",
    ),
    db: Session = Depends(get_db),
):
    return {"alerts": get_alerts(db, include_inactive=include_inactive)}

@router.get(
    "/{city_id}",
    summary="Get alerts for a city",
    description="Returns weather alerts for a selected city.",
    )
def get_city_alerts(
    city_id: str,
    include_inactive: bool = Query(
        default=False,
        description="If true, include inactive/expired alerts as well.",
    ),
    db: Session = Depends(get_db),
):
    try:
        return {
            "cityId": city_id.lower().strip(),
            "alerts": get_alerts(db, city_id=city_id, include_inactive=include_inactive),
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
