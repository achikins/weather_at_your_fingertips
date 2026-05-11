"""
load_to_db.py

Loads cleaned BOM weather data into PostgreSQL.

RULE:
- ONLY use stations already in DB
- NEVER insert new stations
- Drop unknown stations before any processing
"""

import os
import json
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from pathlib import Path


def safe_read_csv(path, name="file"):
    if not os.path.exists(path):
        print(f"[SKIP] {name} not found: {path}")
        return None
    return pd.read_csv(path)


def run_load_to_db():
    load_dotenv()

    def clean_date(val):
        if pd.isna(val):
            return None
        return val

    def delete_file(path, verbose=True):
        try:
            if os.path.exists(path):
                os.remove(path)
                if verbose:
                    print(f"Deleted: {path}")
        except Exception as e:
            print(f"Failed to delete {path}: {e}")

    # --------------------------------------------------
    # CONFIG
    # --------------------------------------------------

    BASE_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    config_path = BASE_DIR / "config.json"

    with open(config_path) as f:
        config = json.load(f)

    CLEAN_DATA_PATH = PROJECT_ROOT / config["clean_data_path"]

    BATCH_SIZE = 5000

    print("=" * 80)
    print("  LOAD BOM DATA → PostgreSQL (STRICT STATION FILTER)")
    print("=" * 80)

    # --------------------------------------------------
    # CONNECT DB
    # --------------------------------------------------
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5432/weather_at_your_fingertips_db")
    print("Connecting using:", db_url)

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    # --------------------------------------------------
    # LOAD CLEANED DATA
    # --------------------------------------------------
    print(f"Reading cleaned data from {CLEAN_DATA_PATH} ...")
    df = pd.read_csv(CLEAN_DATA_PATH, parse_dates=["date"])
    print(f"  {len(df)} rows loaded.\n")

    # --------------------------------------------------
    # LOAD STATIONS FROM DB (MASTER LIST)
    # --------------------------------------------------
    print("Loading existing stations from database ...")

    cur.execute("SELECT station_id, station_name FROM stations")
    station_rows = cur.fetchall()

    station_id_map = {name: sid for sid, name in station_rows}

    print(f"  {len(station_id_map)} stations loaded from DB.\n")

    # --------------------------------------------------
    # FILTER DATASET (IMPORTANT CORE RULE)
    # --------------------------------------------------
    df["station_id"] = df["station_name"].map(station_id_map)

    valid_df = df.dropna(subset=["station_id"]).copy()
    valid_df["station_id"] = valid_df["station_id"].astype(int)

    dropped = len(df) - len(valid_df)

    if dropped > 0:
        print(f"  Dropping {dropped} rows (stations not in DB).")

    df = valid_df

    # --------------------------------------------------
    # DAILY WEATHER INSERT
    # --------------------------------------------------
    print("Inserting into `daily_weather` ...")

    daily_rows = [
        (
            r["station_id"],
            r["date"].date(),
            r.get("evapotranspiration(mm)"),
            r.get("rain(mm)"),
            r.get("maximum_temperature(°C)"),
            r.get("minimum_temperature(°C)"),
            r.get("maximum_relative_humidity(%)"),
            r.get("minimum_relative_humidity(%)"),
            r.get("average_10m_wind_speed(m/sec)"),
        )
        for _, r in df.iterrows()
    ]

    daily_sql = """
        INSERT INTO daily_weather
        (station_id, obs_date, evapotranspiration_mm, rain_mm,
         max_temp_c, min_temp_c, max_humidity_pct, min_humidity_pct,
         avg_wind_speed_mps)
        VALUES %s
        ON CONFLICT (station_id, obs_date) DO UPDATE SET
            evapotranspiration_mm = EXCLUDED.evapotranspiration_mm,
            rain_mm = EXCLUDED.rain_mm,
            max_temp_c = EXCLUDED.max_temp_c,
            min_temp_c = EXCLUDED.min_temp_c,
            max_humidity_pct = EXCLUDED.max_humidity_pct,
            min_humidity_pct = EXCLUDED.min_humidity_pct,
            avg_wind_speed_mps = EXCLUDED.avg_wind_speed_mps
    """

    total_daily = 0
    for i in range(0, len(daily_rows), BATCH_SIZE):
        batch = daily_rows[i:i + BATCH_SIZE]
        execute_values(cur, daily_sql, batch, page_size=BATCH_SIZE)
        total_daily += len(batch)
        print(f"  {total_daily:,} / {len(daily_rows):,} inserted ...", end="\r")

    conn.commit()
    print(f"\n  Done — {total_daily:,} daily_weather rows inserted.\n")

    # --------------------------------------------------
    # MONTHLY AGGREGATES
    # --------------------------------------------------
    print("Computing monthly aggregates ...")

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    monthly = df.groupby(["station_id", "year", "month"]).agg(
        avg_max_temp_c=("maximum_temperature(°C)", "mean"),
        avg_min_temp_c=("minimum_temperature(°C)", "mean"),
        total_rain_mm=("rain(mm)", "sum"),
        avg_min_humidity_pct=("minimum_relative_humidity(%)", "mean"),
        avg_max_humidity_pct=("maximum_relative_humidity(%)", "mean"),
        avg_wind_speed_ms=("average_10m_wind_speed(m/sec)", "mean"),
        days_recorded=("station_id", "count"),
    ).reset_index()

    monthly = monthly.round(2)

    print(f"  {len(monthly)} monthly rows computed.\n")

    monthly_rows = [
        (
            int(r["station_id"]),
            int(r["year"]),
            int(r["month"]),
            float(r["avg_max_temp_c"]),
            float(r["avg_min_temp_c"]),
            float(r["total_rain_mm"]),
            float(r["avg_min_humidity_pct"]),
            float(r["avg_max_humidity_pct"]),
            float(r["avg_wind_speed_ms"]),
            int(r["days_recorded"]),
        )
        for _, r in monthly.iterrows()
    ]

    monthly_sql = """
        INSERT INTO monthly_aggregates
        (station_id, station_year, station_month,
         avg_max_temp_c, avg_min_temp_c, total_rain_mm,
         avg_min_humidity_pct, avg_max_humidity_pct, avg_wind_speed_ms,
         days_recorded)
        VALUES %s
        ON CONFLICT (station_id, station_year, station_month) DO UPDATE SET
            avg_max_temp_c = EXCLUDED.avg_max_temp_c,
            avg_min_temp_c = EXCLUDED.avg_min_temp_c,
            total_rain_mm = EXCLUDED.total_rain_mm,
            avg_min_humidity_pct = EXCLUDED.avg_min_humidity_pct,
            avg_max_humidity_pct = EXCLUDED.avg_max_humidity_pct,
            avg_wind_speed_ms = EXCLUDED.avg_wind_speed_ms,
            days_recorded = EXCLUDED.days_recorded
    """

    total_monthly = 0
    for i in range(0, len(monthly_rows), BATCH_SIZE):
        batch = monthly_rows[i:i + BATCH_SIZE]
        execute_values(cur, monthly_sql, batch, page_size=BATCH_SIZE)
        total_monthly += len(batch)

    conn.commit()
    print(f"  Done — {total_monthly:,} monthly_aggregates rows inserted.\n")

    # --------------------------------------------------
    # CLEANUP
    # --------------------------------------------------
    print("Cleaning up files ...")

    for f in [
        CLEAN_DATA_PATH,
    ]:
        delete_file(f)

    cur.close()
    conn.close()

    print("=" * 80)
    print("  COMPLETE (STRICT MODE)")
    print(f"  • stations used:       {len(station_id_map):,}")
    print(f"  • daily_weather:       {total_daily:,}")
    print(f"  • monthly_aggregates:  {total_monthly:,}")
    print("=" * 80)


if __name__ == "__main__":
    run_load_to_db()