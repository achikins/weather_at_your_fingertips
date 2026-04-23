from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from dependencies import get_db
from services.compare_service import CITY_TO_STATION, build_compare_payload

router = APIRouter(prefix="/compare", tags=["Compare"])

@router.get("/cities")
def get_compare_cities():
    return {"cities": sorted(CITY_TO_STATION.keys())}

@router.get("/")
def get_compare_data(
    city1: str = "sydney",
    city2: str = "melbourne",
    year: int | None = None,
    db: Session = Depends(get_db),
):
    try:
        return build_compare_payload(
            db,
            city1=city1,
            city2=city2,
            year=year,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
