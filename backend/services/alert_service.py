from typing import Any
from sqlalchemy.orm import Session
from models import Alert, Station
from services.weather_service import CITY_TO_STATION, resolve_station_for_city

ALERT_TYPE_LABELS = {
    "heatwave": "Heatwave",
    "heavy_rainfall": "Heavy Rainfall",
    "strong_winds": "Strong Winds",
    "cold_wave": "Cold Wave",
}

ALERT_TITLES = {
    "heatwave": "Extreme Heat Advisory",
    "heavy_rainfall": "Heavy Rainfall Warning",
    "strong_winds": "Strong Wind Warning",
    "cold_wave": "Cold Wave Warning",
}

ALERT_SAFETY_TIPS = {
    "heatwave": [
        "Stay hydrated and avoid prolonged outdoor activity during peak heat.",
        "Heat stress conditions are expected.",
        "Check on vulnerable people and pets.",
    ],
    "heavy_rainfall": [
        "Watch for local flooding and avoid driving through floodwater.",
        "Monitor official weather updates.",
        "Heavy rainfall and localized flooding are possible.",
    ],
    "strong_winds": [
        "Secure loose outdoor items and take extra care when traveling.",
        "Damaging wind conditions are possible.",
        "Stay away from unstable trees and structures.",
    ],
    "cold_wave": [
        "Keep indoor spaces warm and avoid prolonged outdoor exposure.",
        "Layer clothing and cover extremities.",
        "Very cold overnight conditions are expected.",
        "Check on vulnerable people and bring pets indoors.",
    ],
}

def _city_id_for_station_id(station_id: int) -> str | None:
    for city_id, mapped_station_id in CITY_TO_STATION.items():
        if mapped_station_id == station_id:
            return city_id
    return None

def _serialize_alert(alert: Alert, station_name: str | None) -> dict[str, Any]:
    city_id = _city_id_for_station_id(alert.station_id)
    alert_type = alert.alert_type
    type_label = ALERT_TYPE_LABELS.get(alert_type, alert_type.replace("_", " ").title())
    title = ALERT_TITLES.get(alert_type, type_label)

    return {
        "id": f"alert-{alert.alert_id}",
        "cityId": city_id,
        "cityName": station_name,
        "type": type_label,
        "severity": alert.severity,
        "title": title,
        "description": alert.message,
        "issued": alert.start_time.isoformat() if alert.start_time else None,
        "expires": alert.end_time.isoformat() if alert.end_time else None,
        "affectedAreas": [],
        "safetyTips": ALERT_SAFETY_TIPS.get(alert_type, []),
        "isActive": alert.is_active,
    }

def get_alerts(db: Session, city_id: str | None = None) -> list[dict[str, Any]]:
    query = (
        db.query(Alert, Station.station_name)
        .join(Station, Station.station_id == Alert.station_id)
        .filter(Alert.is_active.is_(True))
    )

    if city_id is not None:
        station_id = resolve_station_for_city(db, city_id)
        query = query.filter(Alert.station_id == station_id)

    rows = query.order_by(Alert.start_time.desc()).all()
    return [_serialize_alert(alert, station_name) for alert, station_name in rows]
