from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timezone
from collections import defaultdict
from sqlalchemy import and_, func, text
from database import SessionLocal
from models import Forecast

@dataclass(frozen=True)
class ThresholdRule:
    alert_type: str
    metric: str
    levels: tuple[tuple[float, str], ...]
    comparator: str  # "ge" or "le"
    title: str

RULES: tuple[ThresholdRule, ...] = (
    ThresholdRule(
        alert_type="heatwave",
        metric="pred_max_temp_c",
        levels=((45.0, "extreme"), (40.0, "high"), (35.0, "moderate")),
        comparator="ge",
        title="Heatwave Alert",
    ),
    ThresholdRule(
        alert_type="heavy_rainfall",
        metric="pred_rain_mm",
        levels=((150.0, "extreme"), (100.0, "high"), (50.0, "moderate")),
        comparator="ge",
        title="Heavy Rainfall Alert",
    ),
    ThresholdRule(
        alert_type="strong_winds",
        metric="pred_wind_speed_ms",
        levels=((20.0, "extreme"), (15.0, "high"), (10.0, "moderate")),
        comparator="ge",
        title="Strong Winds Alert",
    ),
    ThresholdRule(
        alert_type="cold_wave",
        metric="pred_min_temp_c",
        levels=((0.0, "high"), (2.0, "moderate")),
        comparator="le",
        title="Cold Wave Alert",
    ),
)

def pick_severity(rule: ThresholdRule, value: float | None) -> str | None:
    if value is None:
        return None

    for threshold, severity in rule.levels:
        if rule.comparator == "ge" and value >= threshold:
            return severity
        if rule.comparator == "le" and value <= threshold:
            return severity
    return None

def build_message(rule: ThresholdRule, metric_value: float, severity: str) -> str:
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

def latest_forecast_rows(db) -> list[Forecast]:
    latest_subq = (
        db.query(
            Forecast.station_id.label("station_id"),
            func.max(Forecast.generated_at).label("latest_generated_at"),
        )
        .group_by(Forecast.station_id)
        .subquery()
    )

    rows = (
        db.query(Forecast)
        .join(  # Latest forecast batch per station
            latest_subq,
            and_(
                Forecast.station_id == latest_subq.c.station_id,
                Forecast.generated_at == latest_subq.c.latest_generated_at,
            ),
        )
        .filter(Forecast.forecast_date >= date.today())
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
    managed_types = tuple(rule.alert_type for rule in RULES)
    params = {
        "station_id": station_id,
        "now": datetime.now(timezone.utc),
    }

    type_filter_sql = ""
    if managed_types:
        placeholders = []
        for i, alert_type in enumerate(managed_types):
            key = f"t{i}"
            params[key] = alert_type
            placeholders.append(f":{key}")
        type_filter_sql = f"AND alert_type IN ({', '.join(placeholders)})"

    keep_filter_sql = ""
    if active_types:
        keep = []
        for i, alert_type in enumerate(sorted(active_types)):
            key = f"k{i}"
            params[key] = alert_type
            keep.append(f":{key}")
        keep_filter_sql = f"AND alert_type NOT IN ({', '.join(keep)})"

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

def upsert_alert(db, station_id: int, rule: ThresholdRule, severity: str, metric_value: float) -> bool:
    now = datetime.now(timezone.utc)

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
                    message = :message,
                    start_time = :now,
                    end_time = NULL,
                    is_active = TRUE
                WHERE alert_id = :alert_id
                """
            ),
            {
                "alert_id": existing[0],
                "severity": severity,
                "message": build_message(rule, metric_value, severity),
                "now": now,
            },
        )
        return False

    db.execute(
        text(
            """
            INSERT INTO alerts (station_id, alert_type, severity, message, start_time, end_time, is_active)
            VALUES (:station_id, :alert_type, :severity, :message, :start_time, NULL, TRUE)
            """
        ),
        {
            "station_id": station_id,
            "alert_type": rule.alert_type,
            "severity": severity,
            "message": build_message(rule, metric_value, severity),
            "start_time": now,
        },
    )
    return True

def run() -> None:
    db = SessionLocal()
    try:
        inserted = 0
        updated = 0
        deactivated = 0

        rows = latest_forecast_rows(db)
        rows_by_station: dict[int, list[Forecast]] = defaultdict(list)
        for row in rows:
            rows_by_station[row.station_id].append(row)

        for station_id, station_rows in rows_by_station.items():
            active_types_for_station: set[str] = set()

            for rule in RULES:
                value = pick_metric_value(rule, station_rows)
                severity = pick_severity(rule, value)
                if severity is None:
                    continue

                active_types_for_station.add(rule.alert_type)
                created = upsert_alert(db, station_id, rule, severity, value)
                if created:
                    inserted += 1
                else:
                    updated += 1

            deactivated += deactivate_missing_alerts(db, station_id, active_types_for_station)

        db.commit()
        print(
            f"Alert generation complete. inserted={inserted}, updated={updated}, deactivated={deactivated}"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
