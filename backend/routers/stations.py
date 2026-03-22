from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models import Station
from dependencies import get_db

router = APIRouter(prefix="/stations", tags=["Stations"])

@router.get("/")
def get_all_stations(db: Session = Depends(get_db)):
    return db.query(Station).all()