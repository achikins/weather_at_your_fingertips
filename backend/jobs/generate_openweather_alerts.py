from database import SessionLocal
from services.alert_service import sync_openweather_alerts

def run() -> None:
    db = SessionLocal()
    try:
        summary = sync_openweather_alerts(db)
        print(
            "OpenWeather alert sync complete. "
            f"cities={summary['cities_processed']}, "
            f"fetched={summary['fetched']}, "
            f"inserted={summary['inserted']}, "
            f"updated={summary['updated']}, "
            f"deactivated={summary['deactivated']}"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()