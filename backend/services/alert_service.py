import json
import os
import re
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from sqlalchemy.orm import Session

from models import Alert, Station
from services.number_utils import to_float
from services.weather_service import CITY_TO_STATION, resolve_station_for_city

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENWEATHER_ALERT_PREFIX = "owm_"
OPENWEATHER_ONECALL_URL = "https://api.openweathermap.org/data/3.0/onecall"
OPENWEATHER_LANG = "en"
OPENWEATHER_TIMEOUT_SECONDS = 6.0

ALERT_TYPE_LABELS = {
    "heatwave": "Heatwave",
    "heavy_rainfall": "Heavy Rainfall",
    "flood": "Flood",
    "strong_winds": "Strong Winds",
    "cold_wave": "Cold Wave",
    "severe_storm": "Severe Storm",
    "thunderstorm": "Thunderstorm",
    "cyclone": "Tropical Cyclone",
    "hail": "Hail",
    "coastal_hazard": "Coastal Hazard",
    "fire_weather": "Fire Weather",
    "fog": "Fog",
    "snow_ice": "Snow and Ice",
}

ALERT_TITLES = {
    "heatwave": "Extreme Heat Advisory",
    "heavy_rainfall": "Heavy Rainfall Warning",
    "flood": "Flood Warning",
    "strong_winds": "Strong Wind Warning",
    "cold_wave": "Cold Weather Warning",
    "severe_storm": "Severe Weather Warning",
    "thunderstorm": "Thunderstorm Warning",
    "cyclone": "Tropical Cyclone Warning",
    "hail": "Hail Warning",
    "coastal_hazard": "Coastal Hazard Warning",
    "fire_weather": "Fire Weather Warning",
    "fog": "Reduced Visibility Warning",
    "snow_ice": "Snow and Ice Warning",
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
    "flood": [
        "Move to higher ground and stay away from rivers, drains, and flood channels.",
        "Never drive or walk through floodwater.",
        "Monitor emergency alerts and evacuation instructions.",
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
    "severe_storm": [
        "Shelter indoors away from windows and unsecured structures.",
        "Avoid unnecessary travel while severe weather is active.",
        "Monitor official emergency weather updates for your area.",
    ],
    "thunderstorm": [
        "Shelter indoors and avoid open fields, trees, and metal structures.",
        "Unplug sensitive electronics if lightning is nearby.",
        "Delay outdoor activity until storms pass.",
    ],
    "cyclone": [
        "Follow local evacuation orders and secure your property early.",
        "Stay indoors away from windows during cyclone conditions.",
        "Keep emergency supplies ready, including water, food, and charged devices.",
    ],
    "hail": [
        "Move vehicles and people under solid cover where possible.",
        "Avoid driving during severe hail conditions.",
        "Stay away from skylights and glass areas.",
    ],
    "coastal_hazard": [
        "Stay clear of beaches, rock platforms, and low coastal paths.",
        "Watch for dangerous surf and sudden wave surges.",
        "Follow warnings from marine and emergency authorities.",
    ],
    "fire_weather": [
        "Avoid ignition sources and follow local fire restrictions.",
        "Prepare an evacuation plan and monitor fire warnings.",
        "Keep emergency essentials ready and accessible.",
    ],
    "fog": [
        "Drive slowly with headlights on low beam and increase following distance.",
        "Avoid unnecessary travel if visibility is severely reduced.",
        "Use extra caution near intersections and pedestrian areas.",
    ],
    "snow_ice": [
        "Avoid non-essential travel on icy or snow-affected roads.",
        "Wear warm layers and protect exposed skin.",
        "Use caution on stairs, paths, and other slippery surfaces.",
    ],
}

OPENWEATHER_TAG_TO_TYPE = {
    "extreme_high_temperature": "heatwave",
    "extreme_low_temperature": "cold_wave",
    "rain": "heavy_rainfall",
    "flood": "flood",
    "wind": "strong_winds",
    "cyclone": "cyclone",
    "tornado": "severe_storm",
    "thunderstorm": "thunderstorm",
    "hail": "hail",
    "coastal_event": "coastal_hazard",
    "snow_ice": "snow_ice",
    "fire": "fire_weather",
    "fog": "fog",
}

DEFAULT_SAFETY_TIPS = [
    "Monitor official weather updates.",
    "Follow advice from emergency services.",
    "Avoid unnecessary travel in affected areas.",
    "Prepare for changing weather conditions.",
]


def _city_id_for_station_id(station_id: int) -> str | None:
    for city_id, mapped_station_id in CITY_TO_STATION.items():
        if mapped_station_id == station_id:
            return city_id
    return None


def _base_type(alert_type: str) -> str:
    if alert_type.startswith(OPENWEATHER_ALERT_PREFIX):
        return alert_type[len(OPENWEATHER_ALERT_PREFIX) :]
    return alert_type


def _clean_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def _format_city_name(name: str | None) -> str | None:
    if not name:
        return None
    trimmed = name.strip()
    if trimmed.isupper() or trimmed.islower():
        return trimmed.title()
    return trimmed


def _format_event_label(event: str) -> str:
    normalized = event.replace("_", " ").strip()
    if not normalized:
        return "Weather Alert"
    if normalized.isupper() or normalized.islower():
        return normalized.title()
    return normalized


def _is_generic_openweather_event(event: str) -> bool:
    normalized = event.lower().strip()
    return normalized in {"weather", "weather alert", "weather warning", "alert", "warning"}


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _serialize_alert(alert: Alert, station_name: str | None) -> dict[str, Any]:
    city_id = _city_id_for_station_id(alert.station_id)
    base_type = _base_type(alert.alert_type)
    description = _clean_text(alert.message)
    city_name = _format_city_name(station_name)
    issued = _as_utc(alert.start_time)
    expires = _as_utc(alert.end_time)

    if alert.alert_type.startswith(OPENWEATHER_ALERT_PREFIX):
        event_label = _format_event_label(base_type)
        safety_type = _map_openweather_type(
            event=event_label,
            tags=[],
            description=description,
        )
        if _is_generic_openweather_event(event_label):
            type_label = ALERT_TYPE_LABELS.get(safety_type, "Weather Alert")
            title = ALERT_TITLES.get(safety_type, type_label)
        else:
            type_label = event_label
            title = event_label
    else:
        safety_type = base_type
        type_label = ALERT_TYPE_LABELS.get(base_type, base_type.replace("_", " ").title())
        title = ALERT_TITLES.get(base_type, type_label)

    return {
        "id": f"alert-{alert.alert_id}",
        "cityId": city_id,
        "cityName": city_name,
        "type": type_label,
        "severity": alert.severity,
        "title": title,
        "description": description,
        "issued": issued.isoformat() if issued else None,
        "expires": expires.isoformat() if expires else None,
        "affectedAreas": [city_name] if city_name else [],
        "safetyTips": ALERT_SAFETY_TIPS.get(safety_type, DEFAULT_SAFETY_TIPS),
        "isActive": alert.is_active,
    }


def _resolve_city_stations(
    db: Session,
    city_id: str | None = None,
) -> list[tuple[str, Station]]:
    if city_id is not None:
        normalized_city_id = city_id.lower().strip()
        station_id = resolve_station_for_city(db, normalized_city_id)
        station = db.query(Station).filter(Station.station_id == station_id).first()
        if station is None:
            return []
        return [(normalized_city_id, station)]

    mapped_station_ids = list(CITY_TO_STATION.values())
    stations = db.query(Station).filter(Station.station_id.in_(mapped_station_ids)).all()
    station_by_id = {station.station_id: station for station in stations}

    city_stations: list[tuple[str, Station]] = []
    for mapped_city_id in sorted(CITY_TO_STATION.keys()):
        station = station_by_id.get(CITY_TO_STATION[mapped_city_id])
        if station is not None:
            city_stations.append((mapped_city_id, station))
    return city_stations


def _to_db_datetime(ts: Any) -> datetime | None:
    if ts is None:
        return None
    try:
        epoch = int(ts)
    except (TypeError, ValueError):
        return None
    return datetime.fromtimestamp(epoch, tz=timezone.utc)


def _map_openweather_type(event: str, tags: list[str], description: str) -> str:
    for raw_tag in tags:
        mapped = OPENWEATHER_TAG_TO_TYPE.get(raw_tag.lower().strip())
        if mapped:
            return mapped

    text = f"{event} {description}".lower()
    if any(token in text for token in ("fire", "bushfire", "wildfire", "red flag")):
        return "fire_weather"
    if any(token in text for token in ("fog", "mist", "visibility")):
        return "fog"
    if any(token in text for token in ("cyclone", "typhoon", "hurricane")):
        return "cyclone"
    if "thunderstorm" in text:
        return "thunderstorm"
    if "hail" in text:
        return "hail"
    if any(token in text for token in ("coastal", "surf", "wave", "marine")):
        return "coastal_hazard"
    if "flood" in text:
        return "flood"
    if any(token in text for token in ("heat", "high temperature", "hot")):
        return "heatwave"
    if any(token in text for token in ("rain", "precipitation", "downpour")):
        return "heavy_rainfall"
    if any(token in text for token in ("snow", "ice", "freezing rain")):
        return "snow_ice"
    if any(token in text for token in ("cold", "freeze", "frost")):
        return "cold_wave"
    if any(token in text for token in ("wind", "gale", "gust")):
        return "strong_winds"
    if any(token in text for token in ("storm", "cyclone", "tornado", "thunder")):
        return "severe_storm"
    return "severe_storm"


def _infer_openweather_severity(event: str, tags: list[str], description: str) -> str:
    text = f"{event} {' '.join(tags)} {description}".lower()

    if any(token in text for token in ("extreme", "catastrophic", "major", "violent", "cyclone", "tornado")):
        return "extreme"
    if any(token in text for token in ("severe", "dangerous", "warning", "hurricane", "storm")):
        return "high"
    if any(token in text for token in ("moderate", "advisory", "watch", "strong")):
        return "moderate"
    if any(token in text for token in ("minor", "light", "possible")):
        return "low"
    return "moderate"


def _fetch_openweather_alerts_for_city(
    city_id: str,
    station: Station,
) -> list[dict[str, Any]] | None:
    if not OPENWEATHER_API_KEY:
        return None

    lat = to_float(station.latitude)
    lon = to_float(station.longitude)
    if lat is None or lon is None:
        return None

    params = {
        "lat": lat,
        "lon": lon,
        "exclude": "current,minutely,hourly,daily",
        "appid": OPENWEATHER_API_KEY,
        "lang": OPENWEATHER_LANG,
    }
    url = f"{OPENWEATHER_ONECALL_URL}?{urlencode(params)}"

    try:
        with urlopen(url, timeout=OPENWEATHER_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None

    raw_alerts = payload.get("alerts") or []
    if not isinstance(raw_alerts, list):
        return None

    mapped_alerts: list[dict[str, Any]] = []
    for raw_alert in raw_alerts:
        if not isinstance(raw_alert, dict):
            continue

        event = str(raw_alert.get("event") or "Weather Alert").strip() or "Weather Alert"
        description = str(raw_alert.get("description") or "OpenWeather alert")
        tags = [str(tag) for tag in (raw_alert.get("tags") or [])]
        severity = _infer_openweather_severity(event=event, tags=tags, description=description)

        start_time = _to_db_datetime(raw_alert.get("start"))
        if start_time is None:
            continue

        mapped_alerts.append(
            {
                "station_id": station.station_id,
                "alert_type": f"{OPENWEATHER_ALERT_PREFIX}{event}",
                "severity": severity,
                "message": description,
                "start_time": start_time,
                "end_time": _to_db_datetime(raw_alert.get("end")),
            }
        )

    return mapped_alerts


def _deactivate_stale_openweather_alerts(
    db: Session,
    station_id: int,
    keep_keys: set[tuple[str, datetime]],
) -> int:
    now = datetime.now(timezone.utc)
    deactivated = 0

    active_openweather = (
        db.query(Alert)
        .filter(
            Alert.station_id == station_id,
            Alert.is_active.is_(True),
            Alert.alert_type.like(f"{OPENWEATHER_ALERT_PREFIX}%"),
        )
        .all()
    )

    for alert in active_openweather:
        start_time = _as_utc(alert.start_time)
        end_time = _as_utc(alert.end_time)
        key = (alert.alert_type, start_time) if start_time is not None else (alert.alert_type, now)
        expired = end_time is not None and end_time <= now
        if key not in keep_keys or expired:
            alert.is_active = False
            if alert.end_time is None:
                alert.end_time = now
            deactivated += 1

    return deactivated


def sync_openweather_alerts(db: Session, city_id: str | None = None) -> dict[str, int]:
    city_stations = _resolve_city_stations(db, city_id=city_id)

    result = {
        "cities_processed": 0,
        "cities_skipped": 0,
        "fetched": 0,
        "inserted": 0,
        "updated": 0,
        "deactivated": 0,
    }

    for mapped_city_id, station in city_stations:
        result["cities_processed"] += 1
        synced = _fetch_openweather_alerts_for_city(mapped_city_id, station)
        if synced is None:
            result["cities_skipped"] += 1
            continue
        result["fetched"] += len(synced)

        keep_keys: set[tuple[str, datetime]] = set()

        for incoming in synced:
            incoming_start_time = _as_utc(incoming["start_time"])
            if incoming_start_time is None:
                continue

            key = (incoming["alert_type"], incoming_start_time)
            keep_keys.add(key)

            existing = (
                db.query(Alert)
                .filter(
                    Alert.station_id == incoming["station_id"],
                    Alert.alert_type == incoming["alert_type"],
                    Alert.start_time == incoming_start_time,
                )
                .first()
            )

            if existing is None:
                db.add(
                    Alert(
                        station_id=incoming["station_id"],
                        alert_type=incoming["alert_type"],
                        severity=incoming["severity"],
                        message=incoming["message"],
                        start_time=incoming_start_time,
                        end_time=_as_utc(incoming["end_time"]),
                        is_active=True,
                    )
                )
                result["inserted"] += 1
                continue

            changed = False
            if existing.severity != incoming["severity"]:
                existing.severity = incoming["severity"]
                changed = True
            if existing.message != incoming["message"]:
                existing.message = incoming["message"]
                changed = True
            incoming_end_time = _as_utc(incoming["end_time"])
            existing_end_time = _as_utc(existing.end_time)
            if existing_end_time != incoming_end_time:
                existing.end_time = incoming_end_time
                changed = True
            if not existing.is_active:
                existing.is_active = True
                changed = True

            if changed:
                result["updated"] += 1

        result["deactivated"] += _deactivate_stale_openweather_alerts(
            db,
            station.station_id,
            keep_keys,
        )

    db.commit()
    return result


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
