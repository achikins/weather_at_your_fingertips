import pandas as pd
import numpy as np


def load_station_mapping(conn):
    station_map = {}
    with conn.cursor() as cur:
        cur.execute("SELECT station_id, station_name FROM stations")
        for station_id, station_name in cur.fetchall():
            station_map[station_id] = station_name
    return station_map


def load_stats(conn, stats_id=1):
    with conn.cursor() as cur:
        cur.execute("SELECT stats FROM model_stats WHERE id = %s", (stats_id,))
        result = cur.fetchone()
        if result is None:
            raise ValueError(f"No stats found with id {stats_id}")
        return result[0]
    

def load_latest_window_data(conn, stats, seq_len=60, history_buffer=120):
    NUMERIC_COLS = [
        "evapotranspiration_mm",
        "rain_mm",
        "max_temp_c",
        "min_temp_c",
        "max_humidity_pct",
        "min_humidity_pct",
        "avg_wind_speed_mps"
    ]
    LAG_STEPS = [1, 2, 3, 7]
    ROLLING_WINDOWS = [7, 14, 30]

    df = pd.read_sql("""
        SELECT *
        FROM daily_weather
        ORDER BY station_id, obs_date
    """, conn)

    df["date"] = pd.to_datetime(df["obs_date"])
    df = df.sort_values(["station_id", "date"])
    df["day_of_year"] = df["date"].dt.dayofyear
    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["sin_day"] = np.sin(2 * np.pi * df["day_of_year"] / 365)
    df["cos_day"] = np.cos(2 * np.pi * df["day_of_year"] / 365)
    df["sin_month"] = np.sin(2 * np.pi * df["month"] / 12)
    df["cos_month"] = np.cos(2 * np.pi * df["month"] / 12)
    df["season"] = ((df["month"] % 12) // 3).astype(int)

    for col in NUMERIC_COLS:
        df[col + "_mask"] = df[col].notna().astype(int)
    
    for col in NUMERIC_COLS:
        mean = stats[col]["mean"]
        std = stats[col]["std"]
        df[col] = (df[col] - mean) / (std + 1e-8)

    for col in NUMERIC_COLS:
        for lag in LAG_STEPS:
            df[f"{col}_lag{lag}"] = df.groupby("station_id")[col].shift(lag)

    for col in NUMERIC_COLS:
        for window in ROLLING_WINDOWS:
            df[f"{col}_rmean{window}"] = df.groupby("station_id")[col].transform(
                lambda x: x.shift(1).rolling(window, min_periods=1).mean())

    df.fillna(0, inplace=True)

    mask_cols = [col + "_mask" for col in NUMERIC_COLS]
    lag_cols = [f"{col}_lag{lag}" for col in NUMERIC_COLS for lag in LAG_STEPS]
    rolling_mean_cols = [f"{col}_rmean{w}" for col in NUMERIC_COLS for w in ROLLING_WINDOWS]
    time_cols = ["sin_day", "cos_day", "sin_month", "cos_month", "day_of_week", "season"]

    FEATURES = (
        NUMERIC_COLS
        + mask_cols
        + lag_cols
        + rolling_mean_cols
        + time_cols
        + ["station_id"]
    )        

    df = df[FEATURES + ["date"]]

    
    return df