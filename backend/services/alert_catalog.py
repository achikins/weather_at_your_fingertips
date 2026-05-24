from __future__ import annotations
from typing import Any

OPENWEATHER_ALERT_PREFIX = "owm_"

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

DEFAULT_SAFETY_TIPS = [
    "Monitor official weather updates.",
    "Follow advice from emergency services.",
    "Avoid unnecessary travel in affected areas.",
    "Prepare for changing weather conditions.",
]

def base_alert_type(alert_type: str) -> str:
    if alert_type.startswith(OPENWEATHER_ALERT_PREFIX):
        return alert_type[len(OPENWEATHER_ALERT_PREFIX) :]
    return alert_type

def is_openweather_alert_type(alert_type: str) -> bool:
    return alert_type.startswith(OPENWEATHER_ALERT_PREFIX)

def format_event_label(event: str) -> str:
    normalized = event.replace("_", " ").strip()
    if not normalized:
        return "Weather Alert"
    if normalized.isupper() or normalized.islower():
        return normalized.title()
    return normalized

def get_alert_type_label(alert_type: str) -> str:
    return ALERT_TYPE_LABELS.get(alert_type, alert_type.replace("_", " ").title())

def get_alert_title(alert_type: str) -> str:
    type_label = get_alert_type_label(alert_type)
    return ALERT_TITLES.get(alert_type, type_label)

def get_alert_safety_tips(alert_type: str) -> list[str]:
    return ALERT_SAFETY_TIPS.get(alert_type, DEFAULT_SAFETY_TIPS)

def normalize_severity(value: Any) -> str | None:
    if value is None:
        return None
    raw = str(value).strip().lower()
    if not raw:
        return None

    allowed = {"low", "moderate", "high", "extreme"}
    if raw in allowed:
        return raw
    if raw in {"very high", "severe", "major", "dangerous"}:
        return "high"
    if raw in {"medium", "med"}:
        return "moderate"
    if raw in {"minor", "small"}:
        return "low"
    if raw in {"catastrophic"}:
        return "extreme"
    return None
