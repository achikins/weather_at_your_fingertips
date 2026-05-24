from datetime import datetime, timezone
import json
from typing import Any
from sqlalchemy import and_, case, or_
from sqlalchemy.orm import Session
from models import Alert, Station
from services.alert_catalog import (
    base_alert_type,
    get_alert_safety_tips,
    get_alert_title,
    get_alert_type_label,
    is_openweather_alert_type,
)
from services.alert_utils import as_utc, clean_text, format_city_name, normalize_string_list
from services.openweather_alert_service import sync_openweather_alerts as sync_openweather_alerts_impl
from services.weather_service import city_id_for_station_id, resolve_station_for_city

def _parse_json_array_text(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return normalize_string_list(decoded, max_items=20)

def _serialize_internal_alert(alert: Alert, city_id: str | None, city_name: str | None) -> dict[str, Any]:
    alert_type = base_alert_type(alert.alert_type)
    type_label = get_alert_type_label(alert_type)
    title = alert.title or get_alert_title(alert_type)
    description = clean_text(alert.message)

    affected_areas = _parse_json_array_text(alert.affected_areas)
    safety_tips = _parse_json_array_text(alert.safety_tips)

    return {
        "id": f"alert-{alert.alert_id}",
        "cityId": city_id,
        "cityName": city_name,
        "type": type_label,
        "severity": alert.severity,
        "title": title,
        "description": description,
        "issued": as_utc(alert.start_time).isoformat() if alert.start_time else None,
        "expires": as_utc(alert.end_time).isoformat() if alert.end_time else None,
        "affectedAreas": affected_areas or ([city_name] if city_name else []),
        "safetyTips": safety_tips or get_alert_safety_tips(alert_type),
        "isActive": alert.is_active,
    }

def _serialize_openweather_alert(alert: Alert, city_id: str | None, city_name: str | None) -> dict[str, Any]:
    type_label = get_alert_type_label(base_alert_type(alert.alert_type))
    description = clean_text(alert.message)

    affected_areas = _parse_json_array_text(alert.affected_areas)
    safety_tips = _parse_json_array_text(alert.safety_tips)

    return {
        "id": f"alert-{alert.alert_id}",
        "cityId": city_id,
        "cityName": city_name,
        "type": type_label,
        "severity": alert.severity,
        "title": alert.title or type_label,
        "description": description,
        "issued": as_utc(alert.start_time).isoformat() if alert.start_time else None,
        "expires": as_utc(alert.end_time).isoformat() if alert.end_time else None,
        "affectedAreas": affected_areas,
        "safetyTips": safety_tips,
        "isActive": alert.is_active,
    }

def _serialize_alert(alert: Alert, station_name: str | None) -> dict[str, Any]:
    city_id = city_id_for_station_id(alert.station_id)
    city_name = format_city_name(station_name)

    if is_openweather_alert_type(alert.alert_type):
        return _serialize_openweather_alert(alert, city_id, city_name)
    return _serialize_internal_alert(alert, city_id, city_name)

def sync_openweather_alerts(db: Session, city_id: str | None = None) -> dict[str, int]:
    return sync_openweather_alerts_impl(db=db, city_id=city_id)

def get_alerts(
    db: Session,
    city_id: str | None = None,
    include_inactive: bool = False,
) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    expired_order = case(
        (
            or_(
                Alert.is_active.is_(False),
                and_(Alert.end_time.is_not(None), Alert.end_time <= now),
            ),
            1,
        ),
        else_=0,
    )

    query = (
        db.query(Alert, Station.station_name)
        .join(Station, Station.station_id == Alert.station_id)
    )

    if not include_inactive:
        query = query.filter(Alert.is_active.is_(True))

    if city_id is not None:
        station_id = resolve_station_for_city(db, city_id)
        query = query.filter(Alert.station_id == station_id)

    rows = query.order_by(expired_order.asc(), Alert.start_time.desc()).all()
    return [_serialize_alert(alert, station_name) for alert, station_name in rows]
