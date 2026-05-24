from __future__ import annotations
from zoneinfo import ZoneInfo

STATE_TO_TZ = {
    "NSW": "Australia/Sydney",
    "ACT": "Australia/Sydney",
    "VIC": "Australia/Melbourne",
    "TAS": "Australia/Hobart",
    "QLD": "Australia/Brisbane",
    "SA": "Australia/Adelaide",
    "WA": "Australia/Perth",
    "NT": "Australia/Darwin",
}

DEFAULT_AUSTRALIA_TZ = "Australia/Sydney"

def timezone_for_state(state: str | None) -> ZoneInfo:
    if state is None:
        return ZoneInfo(DEFAULT_AUSTRALIA_TZ)

    key = state.strip().upper()
    tz_name = STATE_TO_TZ.get(key, DEFAULT_AUSTRALIA_TZ)
    return ZoneInfo(tz_name)
