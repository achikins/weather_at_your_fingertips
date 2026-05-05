import os
import json
import ftplib
import tarfile
import datetime
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import datetime


today_str = datetime.date.today().strftime("%Y-%m-%d")

FTP_HOST = "ftp.bom.gov.au"
FTP_DIR = "anon/gen/clim_data"
FILES_TO_DOWNLOAD = ["IDCKWCDEA0.tgz"]
BASE_PATH = f"{today_str}/tables"

def run_download_data(verbose=True):
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    download_folder = today_str
    if not os.path.exists(download_folder):
        os.makedirs(download_folder, exist_ok=True)
    ftp = ftplib.FTP(FTP_HOST)
    ftp.login()
    ftp.set_pasv(True)
    ftp.cwd(FTP_DIR)
    for filename in FILES_TO_DOWNLOAD:
        local_path = os.path.join(download_folder, filename)
        with open(local_path, "wb") as f:
            ftp.retrbinary(f"RETR {filename}", f.write)
        if filename.endswith((".tgz", ".tar.gz")):
            with tarfile.open(local_path, "r:gz") as tar:
                tar.extractall(path=download_folder, filter="data")
            os.remove(local_path)
        if verbose:
            print(f"Downloaded: {filename}")
    ftp.quit()
    return download_folder


def run_clean_data(download_folder, verbose=True):
    with open("config.json") as f:
        config = json.load(f)
    input_file = config["combined_data_path"]
    output_file = config["clean_data_path"]
    df = pd.read_csv(input_file, low_memory=False)
    df["date"] = pd.to_datetime(df["date"])
    numeric_cols = [
        "evapotranspiration(mm)",
        "rain(mm)",
        "maximum_temperature(°C)",
        "minimum_temperature(°C)",
        "maximum_relative_humidity(%)",
        "minimum_relative_humidity(%)",
        "average_10m_wind_speed(m/sec)",
    ]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    cleaned = []
    for station, g in df.groupby("station_name"):
        g = g.sort_values("date")

        g = g.groupby("date", as_index=False).agg({
            **{c: "mean" for c in numeric_cols},
            "station_name": "first"
        })
        full_dates = pd.date_range(g["date"].min(), g["date"].max(), freq="D")
        g = g.set_index("date").reindex(full_dates)
        g["station_name"] = station
        for c in numeric_cols:
            g[c] = g[c].interpolate(method="time", limit=3, limit_direction="both")
        g = g.reset_index().rename(columns={"index": "date"})
        cleaned.append(g)
    cleaned_df = pd.concat(cleaned)
    cleaned_df.to_csv(output_file, index=False)
    if verbose:
        print(f"Cleaned data saved: {output_file}")
    return output_file


def run_load_to_db(clean_file):
    load_dotenv()
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    df = pd.read_csv(clean_file, parse_dates=["date"])
    # -------------------------
    # GET EXISTING STATIONS ONLY
    # -------------------------
    cur.execute("SELECT station_id, station_name FROM stations")
    station_map = {name: sid for sid, name in cur.fetchall()}
    # ❌ HARD FILTER: no unknown stations allowed
    df = df[df["station_name"].isin(station_map)]
    df["station_id"] = df["station_name"].map(station_map)
    df = df.dropna(subset=["station_id"])
    df["station_id"] = df["station_id"].astype(int)
    # -------------------------
    # STATIONS TABLE (UPDATE ONLY)
    # -------------------------
    station_file = json.load(open("config.json"))["station_dataset_path"]
    station_df = pd.read_csv(station_file)
    for _, r in station_df.iterrows():
        if r["station_name"] not in station_map:
            continue  # ❌ skip new stations completely
        cur.execute("""
            UPDATE stations
            SET aus_state=%s,
                latitude=%s,
                longitude=%s,
                elevation_m=%s,
                starting_date=%s,
                end_date=%s,
                coverage_pct=%s
            WHERE station_name=%s
        """, (
            r.get("aus_state"),
            r.get("latitude"),
            r.get("longitude"),
            r.get("elevation_m"),
            r.get("starting_date"),
            r.get("end_date"),
            r.get("coverage_pct"),
            r["station_name"]
        ))
    # -------------------------
    # DAILY WEATHER
    # -------------------------
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
            r.get("average_10m_wind_speed(m/sec)")
        )
        for _, r in df.iterrows()
    ]
    execute_values(cur, """
        INSERT INTO daily_weather
        VALUES %s
        ON CONFLICT (station_id, obs_date) DO UPDATE SET
            evapotranspiration_mm = EXCLUDED.evapotranspiration_mm,
            rain_mm = EXCLUDED.rain_mm,
            max_temp_c = EXCLUDED.max_temp_c,
            min_temp_c = EXCLUDED.min_temp_c,
            max_humidity_pct = EXCLUDED.max_humidity_pct,
            min_humidity_pct = EXCLUDED.min_humidity_pct,
            avg_wind_speed_mps = EXCLUDED.avg_wind_speed_mps
    """, daily_rows, page_size=5000)
    # -------------------------
    # MONTHLY AGGREGATES
    # -------------------------
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    monthly = df.groupby(["station_id", "year", "month"]).mean(numeric_only=True).reset_index()
    monthly_rows = [
        tuple(x) for x in monthly.to_numpy()
    ]
    execute_values(cur, """
        INSERT INTO monthly_aggregates
        VALUES %s
        ON CONFLICT (station_id, station_year, station_month)
        DO UPDATE SET
            avg_max_temp_c = EXCLUDED.avg_max_temp_c,
            avg_min_temp_c = EXCLUDED.avg_min_temp_c,
            total_rain_mm = EXCLUDED.total_rain_mm,
            avg_min_humidity_pct = EXCLUDED.avg_min_humidity_pct,
            avg_max_humidity_pct = EXCLUDED.avg_max_humidity_pct,
            avg_wind_speed_ms = EXCLUDED.avg_wind_speed_ms,
            days_recorded = EXCLUDED.days_recorded
    """, monthly_rows, page_size=5000)
    conn.commit()
    cur.close()
    conn.close()
    print("DB load complete (STRICT MODE: no new stations allowed)")