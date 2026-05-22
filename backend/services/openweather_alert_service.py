from __future__ import annotations
import json
import os
import re
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen
from google import genai
from sqlalchemy.orm import Session
from models import Alert
from services.alert_catalog import (
    OPENWEATHER_ALERT_PREFIX,
    format_event_label,
    normalize_severity,
)
from services.alert_utils import as_utc, clean_text, format_city_name, normalize_string_list
from services.number_utils import to_float
from services.weather_service import resolve_city_stations

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENWEATHER_ONECALL_URL = "https://api.openweathermap.org/data/3.0/onecall"
OPENWEATHER_LANG = "en"
OPENWEATHER_TIMEOUT_SECONDS = 6.0
GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_GEMINI_AFFECTED_AREAS_LIMIT = 6
DEFAULT_GEMINI_SAFETY_TIPS_LIMIT = 5
GEMINI_CLIENT = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def _clean_area_name(area: str) -> str:
    cleaned = clean_text(area)
    if not cleaned:
        return ""
    cleaned = re.sub(r"\([^)]*\)", "", cleaned)
    cleaned = re.sub(r"\[[^\]]*\]", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,;:-")
    return cleaned

def _clean_title(title: str, city_name: str) -> str:
    cleaned = clean_text(title)
    if not cleaned:
        return ""

    city_pattern = re.escape(city_name.strip())
    suffix_patterns = (
        rf"\s*[-–—,:]\s*{city_pattern}\s*$",
        rf"\s+\(\s*{city_pattern}\s*\)\s*$",
        rf"\s+for\s+{city_pattern}\s*$",
        rf"\s+in\s+{city_pattern}\s*$",
    )
    for pattern in suffix_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned

def _normalize_alert_type(raw_type: Any) -> str | None:
    if raw_type is None:
        return None
    normalized = clean_text(str(raw_type))
    if not normalized:
        return None
    if normalized.lower().startswith(OPENWEATHER_ALERT_PREFIX):
        normalized = normalized[len(OPENWEATHER_ALERT_PREFIX) :].strip()
    return normalized or None

def _parse_gemini_json(text: str | None) -> dict[str, Any] | None:
    cleaned = clean_text(text)
    if not cleaned:
        return None
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None

def _to_db_datetime(ts: Any) -> datetime | None:
    if ts is None:
        return None
    try:
        epoch = int(ts)
    except (TypeError, ValueError):
        return None
    return datetime.fromtimestamp(epoch, tz=timezone.utc)

def enrich_alert_with_gemini(
    *,
    city_name: str,
    event: str,
    description: str,
    start_time: datetime,
    end_time: datetime | None,
) -> dict[str, Any] | None:
    if GEMINI_CLIENT is None:
        return None

    prompt = f"""
Convert this weather alert into frontend JSON.

Rules:
- Return JSON only.
- Do not invent official facts.
- Keep the description short but faithful.
- Extract affected areas from the description if present.
- Safety tips must be practical and conservative.
- Use Australian English.
- Severity must be one of: low, moderate, high, extreme.
- Title must NOT include city suffixes like "- {city_name}" or "( {city_name} )".
- Affected areas must be plain names only (no brackets or parenthesised qualifiers).

Style examples (follow this style):
Example 1:
{{"alertType":"coastal_hazard","title":"Coastal Hazard Warning","severity":"high","description":"Damaging surf conditions are expected along exposed beaches, with a risk of coastal erosion and dangerous waves.","affectedAreas":["Gold Coast","Noosa Heads","Rainbow Beach"],"safetyTips":["Stay clear of beaches, rock platforms, and low coastal paths.","Watch for dangerous surf and sudden wave surges.","Follow warnings from marine and emergency authorities."]}}
Example 2:
{{"alertType":"thunderstorm","title":"Thunderstorm Warning","severity":"high","description":"Severe thunderstorms may bring damaging winds, heavy rain, and frequent lightning this afternoon.","affectedAreas":["Brisbane","Ipswich","Logan"],"safetyTips":["Shelter indoors and avoid open fields, trees, and metal structures.","Unplug sensitive electronics if lightning is nearby.","Delay outdoor activity until storms pass."]}}
Example 3:
{{"alertType":"heatwave","title":"Extreme Heat Advisory","severity":"moderate","description":"Hot conditions are expected over the next two days, increasing heat stress risk.","affectedAreas":["Melbourne","Geelong"],"safetyTips":["Stay hydrated and avoid prolonged outdoor activity during peak heat.","Check on vulnerable people and pets.","Monitor official weather updates."]}}

Input:
City: {city_name}
Event: {event}
Description: {description}
Start: {start_time.isoformat()}
End: {end_time.isoformat() if end_time else None}

Required JSON keys:
alertType, title, severity, description, affectedAreas, safetyTips
""".strip()

    try:
        response = GEMINI_CLIENT.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
    except Exception as exc:
        print(f"[openweather_sync] reason=gemini_call_failed model={GEMINI_MODEL} error={exc}")
        return None

    raw_text = getattr(response, "text", None)
    payload = _parse_gemini_json(raw_text)
    if not isinstance(payload, dict):
        preview = clean_text(raw_text)[:240] if raw_text else ""
        print(f"[openweather_sync] reason=gemini_invalid_json preview={preview!r}")
        return None

    alert_type = _normalize_alert_type(payload.get("alertType"))
    title = _clean_title(
        clean_text(payload.get("title")) or format_event_label(event),
        city_name=city_name,
    )
    cleaned_description = clean_text(payload.get("description"))
    severity = normalize_severity(payload.get("severity"))
    affected_areas = [
        _clean_area_name(area)
        for area in normalize_string_list(
        payload.get("affectedAreas"),
        max_items=DEFAULT_GEMINI_AFFECTED_AREAS_LIMIT,
    )
    ]
    affected_areas = [area for area in affected_areas if area]
    safety_tips = normalize_string_list(
        payload.get("safetyTips"),
        max_items=DEFAULT_GEMINI_SAFETY_TIPS_LIMIT,
    )

    if alert_type is None or severity is None or not cleaned_description or not title:
        print(
            "[openweather_sync] reason=gemini_invalid_fields "
            f"alert_type={alert_type!r} severity={severity!r} "
            f"title_present={bool(title)} description_present={bool(cleaned_description)}"
        )
        return None

    return {
        "alert_type": alert_type,
        "title": title,
        "severity": severity,
        "message": cleaned_description,
        "affected_areas": json.dumps(affected_areas),
        "safety_tips": json.dumps(safety_tips),
    }

def _fetch_openweather_alerts_for_city(
    city_id: str,
    station: Station,
) -> list[dict[str, Any]] | None:
    if not OPENWEATHER_API_KEY or GEMINI_CLIENT is None:
        print(
            "[openweather_sync] "
            f"city={city_id} reason=missing_key_or_client "
            f"openweather_key={'set' if bool(OPENWEATHER_API_KEY) else 'missing'} "
            f"gemini_client={'set' if GEMINI_CLIENT is not None else 'missing'}"
        )
        return None

    lat = to_float(station.latitude)
    lon = to_float(station.longitude)
    if lat is None or lon is None:
        print(
            "[openweather_sync] "
            f"city={city_id} reason=missing_station_coordinates "
            f"station_id={station.station_id}"
        )
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
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"[openweather_sync] city={city_id} reason=openweather_request_failed error={exc}")
        return None

    raw_alerts = payload.get("alerts") or []
    if not isinstance(raw_alerts, list):
        print(f"[openweather_sync] city={city_id} reason=invalid_openweather_alerts_payload")
        return None

    mapped_alerts: list[dict[str, Any]] = []
    for raw_alert in raw_alerts:
        if not isinstance(raw_alert, dict):
            continue

        event = str(raw_alert.get("event") or "Weather Alert").strip() or "Weather Alert"
        description = str(raw_alert.get("description") or "OpenWeather alert")

        start_time = _to_db_datetime(raw_alert.get("start"))
        if start_time is None:
            print(f"[openweather_sync] city={city_id} reason=missing_alert_start_time event={event!r}")
            continue
        end_time = _to_db_datetime(raw_alert.get("end"))
        city_name = format_city_name(station.station_name) or city_id

        gemini_data = enrich_alert_with_gemini(
            city_name=city_name,
            event=event,
            description=description,
            start_time=start_time,
            end_time=end_time,
        )
        if gemini_data is None:
            print(f"[openweather_sync] city={city_id} reason=gemini_enrichment_failed event={event!r}")
            continue

        mapped_alerts.append(
            {
                "station_id": station.station_id,
                "alert_type": f"{OPENWEATHER_ALERT_PREFIX}{gemini_data['alert_type']}",
                "title": gemini_data["title"],
                "severity": gemini_data["severity"],
                "message": gemini_data["message"],
                "start_time": start_time,
                "end_time": end_time,
                "affected_areas": gemini_data["affected_areas"],
                "safety_tips": gemini_data["safety_tips"],
            }
        )

    if raw_alerts and not mapped_alerts:
        print(
            "[openweather_sync] "
            f"city={city_id} reason=no_mappable_alerts "
            f"raw_alert_count={len(raw_alerts)}"
        )
        return None
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
        start_time = as_utc(alert.start_time)
        end_time = as_utc(alert.end_time)
        key = (alert.alert_type, start_time) if start_time is not None else (alert.alert_type, now)
        expired = end_time is not None and end_time <= now
        if key not in keep_keys or expired:
            alert.is_active = False
            if alert.end_time is None:
                alert.end_time = now
            deactivated += 1

    return deactivated

def sync_openweather_alerts(db: Session, city_id: str | None = None) -> dict[str, int]:
    city_stations = resolve_city_stations(db, city_id=city_id)

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
        city_inserted = 0
        city_updated = 0
        city_deactivated = 0
        city_fetched = 0

        synced = _fetch_openweather_alerts_for_city(mapped_city_id, station)
        if synced is None:
            result["cities_skipped"] += 1
            print(
                "[openweather_sync] "
                f"city={mapped_city_id} done "
                "status=skipped fetched=0 inserted=0 updated=0 deactivated=0"
            )
            continue
        city_fetched = len(synced)
        result["fetched"] += city_fetched

        keep_keys: set[tuple[str, datetime]] = set()

        for incoming in synced:
            incoming_start_time = as_utc(incoming["start_time"])
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
                        title=incoming["title"],
                        severity=incoming["severity"],
                        message=incoming["message"],
                        start_time=incoming_start_time,
                        end_time=as_utc(incoming["end_time"]),
                        affected_areas=incoming["affected_areas"],
                        safety_tips=incoming["safety_tips"],
                        is_active=True,
                    )
                )
                result["inserted"] += 1
                city_inserted += 1
                continue

            changed = False
            for field in ("severity", "message", "title", "affected_areas", "safety_tips"):
                if getattr(existing, field) != incoming[field]:
                    setattr(existing, field, incoming[field])
                    changed = True
            incoming_end_time = as_utc(incoming["end_time"])
            existing_end_time = as_utc(existing.end_time)
            if existing_end_time != incoming_end_time:
                existing.end_time = incoming_end_time
                changed = True
            if not existing.is_active:
                existing.is_active = True
                changed = True

            if changed:
                result["updated"] += 1
                city_updated += 1

        deactivated_now = _deactivate_stale_openweather_alerts(
            db,
            station.station_id,
            keep_keys,
        )
        result["deactivated"] += deactivated_now
        city_deactivated += deactivated_now

        print(
            "[openweather_sync] "
            f"city={mapped_city_id} done "
            f"fetched={city_fetched} inserted={city_inserted} "
            f"updated={city_updated} deactivated={city_deactivated}"
        )

    db.commit()
    return result
