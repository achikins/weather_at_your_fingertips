"""
load_to_db.py

Loads cleaned BOM weather data into the PostgreSQL database

Run AFTER
  1. download_data.py
  2. station_summary.py
  3. download_station_data.py
  4. combine_data.py
  5. clean_data.py

And AFTER running the SQL schema file to create the tables

Usage:
    python load_to_db.py

Requires:
    pip install psycopg2-binary pandas python-dotenv
"""

import os
import json
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

#config

# Get folder where this script is
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

with open(CONFIG_PATH) as f:
    config = json.load(f)

CLEAN_DATA_PATH = os.path.join(BASE_DIR, config["clean_data_path"])
STATION_SUMMARY_PATH = os.path.join(BASE_DIR, config["station_summary_path"])
STATION_DATA_PATH = os.path.join(BASE_DIR, config["station_dataset_path"])

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     os.getenv("DB_PORT", "5432"),
    "dbname":   os.getenv("DB_NAME", "weather_at_your_fingertips_db"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
}

BATCH_SIZE = 5000  

# column mapping: clean_data.csv to DB columns 

print("=" * 80)
print("  LOAD BOM DATA → PostgreSQL")
print("=" * 80)


#1. connect 

print(f"\nConnecting to {DB_CONFIG['dbname']}@{DB_CONFIG['host']}:{DB_CONFIG['port']} ...")
conn = psycopg2.connect(**DB_CONFIG)
conn.autocommit = False
cur = conn.cursor()
print("Connected.\n")


#2. load cleaned data and build stations from it

print(f"Reading cleaned data from {CLEAN_DATA_PATH} ...")
df = pd.read_csv(CLEAN_DATA_PATH, parse_dates=["date"])
print(f"  {len(df)} rows loaded.\n")

print("Loading station data ...\n")
station_df = pd.read_csv(STATION_DATA_PATH)

print(f"Inserting {len(station_df)} stations into `stations` table ...")
station_id_map = {}

for _, row in station_df.iterrows():
    cur.execute(
        """
        INSERT INTO stations (station_name, state, latitude, longitude, elevation_m, start_date, end_date, coverage_pct)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        RETURNING station_id
        """,
        (
            row["station_name"], # required
            row.get("state"),
            row.get("latitude"),
            row.get("longitude"),
            row.get("elevation_m"),
            row.get("start_date"),
            row.get("end_date"),
            row.get("coverage_pct"),
        ),
    )
    result = cur.fetchone()
    if result:
        station_id_map[row["station_name"]] = result[0]

# Also fetch any that already existed (ON CONFLICT hit)
cur.execute("SELECT station_id, station_name FROM stations")
for sid, sname in cur.fetchall():
    station_id_map[sname] = sid

conn.commit()
print(f"  {len(station_id_map)} stations in DB.\n")


#load daily weather

# Map station names to IDs
df["station_id"] = df["station_name"].map(station_id_map)
unmapped = df["station_id"].isna().sum()
if unmapped:
    print(f"  Warning: {unmapped} rows have no matching station — skipping those.")
    df = df.dropna(subset=["station_id"])
df["station_id"] = df["station_id"].astype(int)

print("Inserting into `daily_weather` table ...")
daily_rows = []
for _, r in df.iterrows():
    daily_rows.append((
        r["station_id"],
        r["date"].date(),
        r.get("rain(mm)"),
        r.get("maximum_temperature(°C)"),
        r.get("minimum_temperature(°C)"),
        r.get("maximum_relative_humidity(%)"),
        r.get("minimum_relative_humidity(%)"),
        r.get("average_10m_wind_speed(m/sec)"),
    ))

insert_sql = """
    INSERT INTO daily_weather
        (station_id, obs_date, rain_mm, max_temp_c, min_temp_c,
         max_humidity_pct, min_humidity_pct, avg_wind_speed_mps)
    VALUES %s
    ON CONFLICT (station_id, obs_date) DO UPDATE SET
        rain_mm          = EXCLUDED.rain_mm,
        max_temp_c       = EXCLUDED.max_temp_c,
        min_temp_c       = EXCLUDED.min_temp_c,
        max_humidity_pct = EXCLUDED.max_humidity_pct,
        min_humidity_pct = EXCLUDED.min_humidity_pct,
        avg_wind_speed_mps = EXCLUDED.avg_wind_speed_mps
"""

total_inserted = 0
for i in range(0, len(daily_rows), BATCH_SIZE):
    batch = daily_rows[i : i + BATCH_SIZE]
    execute_values(cur, insert_sql, batch, page_size=BATCH_SIZE)
    total_inserted += len(batch)
    print(f"  {total_inserted:,} / {len(daily_rows):,} rows inserted ...", end="\r")

conn.commit()
print(f"\n  Done — {total_inserted:,} daily_weather rows inserted.\n")


#4. Compute and load monthly aggregates 

print("Computing monthly aggregates ...")
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month

monthly = df.groupby(["station_id", "year", "month"]).agg(
    avg_max_temp_c       = ("maximum_temperature(°C)", "mean"),
    avg_min_temp_c       = ("minimum_temperature(°C)", "mean"),
    total_rain_mm        = ("rain(mm)", "sum"),
    avg_min_humidity_pct = ("minimum_relative_humidity(%)", "mean"),
    avg_max_humidity_pct = ("maximum_relative_humidity(%)", "mean"),
    avg_wind_speed_ms    = ("average_10m_wind_speed(m/sec)", "mean"),
    days_recorded        = ("station_id", "count"),
).reset_index()

monthly = monthly.round(2)

print(f"  {len(monthly)} monthly rows computed.\n")

print("Inserting into `monthly_aggregates` table ...")
monthly_rows = []
for _, r in monthly.iterrows():
    monthly_rows.append((
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
))

monthly_sql = """
    INSERT INTO monthly_aggregates
        (station_id, station_year, station_month,
         avg_max_temp_c, avg_min_temp_c, total_rain_mm,
         avg_min_humidity_pct, avg_max_humidity_pct, avg_wind_speed_ms,
         days_recorded)
    VALUES %s
    ON CONFLICT (station_id, station_year, station_month) DO UPDATE SET
        avg_max_temp_c       = EXCLUDED.avg_max_temp_c,
        avg_min_temp_c       = EXCLUDED.avg_min_temp_c,
        total_rain_mm        = EXCLUDED.total_rain_mm,
        avg_min_humidity_pct = EXCLUDED.avg_min_humidity_pct,
        avg_max_humidity_pct = EXCLUDED.avg_max_humidity_pct,
        avg_wind_speed_ms    = EXCLUDED.avg_wind_speed_ms,
        days_recorded        = EXCLUDED.days_recorded
"""

total_monthly = 0
for i in range(0, len(monthly_rows), BATCH_SIZE):
    batch = monthly_rows[i : i + BATCH_SIZE]
    execute_values(cur, monthly_sql, batch, page_size=BATCH_SIZE)
    total_monthly += len(batch)

conn.commit()
print(f"  Done — {total_monthly:,} monthly_aggregates rows inserted.\n")


#5. Cleanup

cur.close()
conn.close()

print("=" * 80)
print("  COMPLETE")
print(f"  • stations:            {len(station_id_map):,}")
print(f"  • daily_weather:       {total_inserted:,}")
print(f"  • monthly_aggregates:  {total_monthly:,}")
print(f"  • forecasts:           (populated by your LSTM model)")
print(f"  • alerts:              (auto-generated from forecasts)")
print("=" * 80)
