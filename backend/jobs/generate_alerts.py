from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from collections import defaultdict
import json
from sqlalchemy import and_, func, text
from database import SessionLocal
from models import Forecast, Station
from services.alert_catalog import get_alert_safety_tips, get_alert_title
from services.station_timezones import timezone_for_state

@dataclass(frozen=True)
class ThresholdRule:
    alert_type: str
    metric: str
    levels: tuple[tuple[float, str], ...]
    comparator: str  # "ge" or "le"

RULES: tuple[ThresholdRule, ...] = (
    ThresholdRule(
        alert_type="heatwave",
        metric="pred_max_temp_c",
        levels=((45.0, "extreme"), (40.0, "high"), (35.0, "moderate")),
        comparator="ge",
    ),
    ThresholdRule(
        alert_type="heavy_rainfall",
        metric="pred_rain_mm",
        levels=((150.0, "extreme"), (100.0, "high"), (50.0, "moderate")),
        comparator="ge",
    ),
    ThresholdRule(
        alert_type="strong_winds",
        metric="pred_wind_speed_ms",
        levels=((20.0, "extreme"), (15.0, "high"), (10.0, "moderate")),
        comparator="ge",
    ),
    ThresholdRule(
        alert_type="cold_wave",
        metric="pred_min_temp_c",
        levels=(
            (-5.0, "extreme"),
            (-2.0, "high"),
            (0.0, "moderate"),
            (2.0, "low"),
        ),
        comparator="le",
    ),
)

def managed_alert_types() -> tuple[str, ...]:
    return tuple(rule.alert_type for rule in RULES)

def bind_placeholders(
    *,
    params: dict[str, object],
    prefix: str,
    values: list[str] | tuple[str, ...],
) -> str:
    placeholders: list[str] = []
    for i, value in enumerate(values):
        key = f"{prefix}{i}"
        params[key] = value
        placeholders.append(f":{key}")
    return ", ".join(placeholders)

def pick_severity(rule: ThresholdRule, value: float | None) -> str | None:
    if value is None:
        return None

    for threshold, severity in rule.levels:
        if rule.comparator == "ge" and value >= threshold:
            return severity
        if rule.comparator == "le" and value <= threshold:
            return severity
    return None

def build_message(rule: ThresholdRule, metric_value: float) -> str:
    if rule.alert_type == "heatwave":
        return (
            f"Forecast temperature may reach {metric_value:.1f}°C. "
            "Heat stress conditions are expected."
        )

    if rule.alert_type == "heavy_rainfall":
        return (
            f"Forecast rainfall may reach {metric_value:.1f} mm. "
            "Heavy rainfall and localized flooding are possible."
        )

    if rule.alert_type == "strong_winds":
        return (
            f"Forecast average wind speed may reach {metric_value:.1f} m/s. "
            "Damaging wind conditions are possible."
        )

    if rule.alert_type == "cold_wave":
        return (
            f"Forecast minimum temperature may drop to {metric_value:.1f}°C. "
            "Very cold overnight conditions are expected."
        )

def next_local_midnight_utc(*, station_state: str | None, now_utc: datetime) -> datetime:
    tz = timezone_for_state(station_state)
    local_now = now_utc.astimezone(tz)
    next_day = local_now.date() + timedelta(days=1)
    next_midnight_local = datetime.combine(next_day, time.min, tzinfo=tz)
    return next_midnight_local.astimezone(timezone.utc)

def latest_forecast_rows(db) -> list[tuple[Forecast, str | None]]:
    latest_subq = (
        db.query(
            Forecast.station_id.label("station_id"),
            func.max(Forecast.generated_at).label("latest_generated_at"),
        )
        .group_by(Forecast.station_id)
        .subquery()
    )

    rows = (
        db.query(Forecast, Station.state)
        .join(  # Latest forecast batch per station
            latest_subq,
            and_(
                Forecast.station_id == latest_subq.c.station_id,
                Forecast.generated_at == latest_subq.c.latest_generated_at,
            ),
        )
        .join(Station, Station.station_id == Forecast.station_id)
        .order_by(Forecast.station_id.asc(), Forecast.forecast_date.asc(), Forecast.horizon_days.asc())
        .all()
    )
    return rows

def pick_metric_value(rule: ThresholdRule, rows: list[Forecast]) -> float | None:
    values: list[float] = []
    for row in rows:
        raw = getattr(row, rule.metric)
        if raw is not None:
            values.append(float(raw))
    if not values:
        return None
    if rule.comparator == "ge":
        return max(values)
    return min(values)

def deactivate_missing_alerts(db, station_id: int, active_types: set[str]) -> int:
    managed_types = managed_alert_types()
    params = {
        "station_id": station_id,
        "now": datetime.now(timezone.utc),
    }

    type_filter_sql = ""
    if managed_types:
        type_filter_sql = (
            f"AND alert_type IN ({bind_placeholders(params=params, prefix='t', values=managed_types)})"
        )

    keep_filter_sql = ""
    if active_types:
        keep_filter_sql = (
            f"AND alert_type NOT IN ({bind_placeholders(params=params, prefix='k', values=sorted(active_types))})"
        )

    result = db.execute(
        text(
            f"""
            UPDATE alerts
            SET is_active = FALSE, end_time = :now
            WHERE station_id = :station_id
              AND is_active = TRUE
              {type_filter_sql}
              {keep_filter_sql}
            """
        ),
        params,
    )
    return result.rowcount or 0

def upsert_alert(
    db,
    station_id: int,
    rule: ThresholdRule,
    severity: str,
    metric_value: float,
    expires_at: datetime,
) -> bool:
    now = datetime.now(timezone.utc)
    title = get_alert_title(rule.alert_type)
    safety_tips = json.dumps(get_alert_safety_tips(rule.alert_type))

    existing = db.execute(
        text(
            """
            SELECT alert_id
            FROM alerts
            WHERE station_id = :station_id
              AND alert_type = :alert_type
              AND is_active = TRUE
            ORDER BY start_time DESC
            LIMIT 1
            """
        ),
        {"station_id": station_id, "alert_type": rule.alert_type},
    ).fetchone()

    if existing:
        db.execute(
            text(
                """
                UPDATE alerts
                SET severity = :severity,
                    title = :title,
                    message = :message,
                    safety_tips = :safety_tips,
                    end_time = :end_time,
                    is_active = TRUE
                WHERE alert_id = :alert_id
                """
            ),
            {
                "alert_id": existing[0],
                "severity": severity,
                "title": title,
                "message": build_message(rule, metric_value),
                "safety_tips": safety_tips,
                "end_time": expires_at,
            },
        )
        return False

    db.execute(
        text(
            """
            INSERT INTO alerts (station_id, alert_type, title, severity, message, safety_tips, start_time, end_time, is_active)
            VALUES (:station_id, :alert_type, :title, :severity, :message, :safety_tips, :start_time, :end_time, TRUE)
            """
        ),
        {
            "station_id": station_id,
            "alert_type": rule.alert_type,
            "title": title,
            "severity": severity,
            "message": build_message(rule, metric_value),
            "safety_tips": safety_tips,
            "start_time": now,
            "end_time": expires_at,
        },
    )
    return True

def stations_with_active_managed_alerts(db) -> set[int]:
    managed_types = managed_alert_types()
    if not managed_types:
        return set()

    params: dict[str, object] = {}
    placeholders = bind_placeholders(params=params, prefix="t", values=managed_types)

    rows = db.execute(
        text(
            f"""
            SELECT DISTINCT station_id
            FROM alerts
            WHERE is_active = TRUE
              AND alert_type IN ({placeholders})
            """
        ),
        params,
    ).fetchall()
    return {int(row[0]) for row in rows}

def run() -> None:
    db = SessionLocal()
    try:
        inserted = 0
        updated = 0
        deactivated = 0
        now_utc = datetime.now(timezone.utc)

        rows = latest_forecast_rows(db)
        rows_by_station: dict[int, list[Forecast]] = defaultdict(list)
        state_by_station: dict[int, str | None] = {}
        for row, station_state in rows:
            rows_by_station[row.station_id].append(row)
            if row.station_id not in state_by_station:
                state_by_station[row.station_id] = station_state

        for station_id, station_rows in rows_by_station.items():
            station_state = state_by_station.get(station_id)
            local_today = now_utc.astimezone(timezone_for_state(station_state)).date()
            today_rows = [row for row in station_rows if row.forecast_date == local_today]

            if not today_rows:
                deactivated += deactivate_missing_alerts(db, station_id, set())
                continue

            active_types_for_station: set[str] = set()
            expires_at = next_local_midnight_utc(station_state=station_state, now_utc=now_utc)

            for rule in RULES:
                value = pick_metric_value(rule, today_rows)
                severity = pick_severity(rule, value)
                if severity is None:
                    continue

                active_types_for_station.add(rule.alert_type)
                created = upsert_alert(
                    db,
                    station_id,
                    rule,
                    severity,
                    value,
                    expires_at=expires_at,
                )
                if created:
                    inserted += 1
                else:
                    updated += 1

            deactivated += deactivate_missing_alerts(db, station_id, active_types_for_station)

        # If a station has no forecast row for today, close any managed alerts for it
        stations_with_forecast = set(rows_by_station.keys())
        for station_id in stations_with_active_managed_alerts(db) - stations_with_forecast:
            deactivated += deactivate_missing_alerts(db, station_id, set())

        db.commit()
        print(
            f"Alert generation complete. inserted={inserted}, updated={updated}, deactivated={deactivated}"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
