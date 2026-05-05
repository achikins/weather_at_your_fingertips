import numpy as np
import pandas as pd
import json
import os
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

def run_prepare_transformer_data(verbose=True):
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")
    print("Connecting using:", DATABASE_URL)
    conn = psycopg2.connect(DATABASE_URL)

    config_path = "config.json"
    try:
        with open(config_path) as f:
            config = json.load(f)

        LAG_STEPS = [1, 2, 3, 7]
        ROLLING_WINDOWS = [7, 14, 30]
        TRAIN_FILE = config["train_path"]
        VAL_FILE = config["val_path"]
        TEST_FILE = config["test_path"]

        df = pd.read_sql("""
            SELECT *
            FROM daily_weather
        """, conn)

        NUMERIC_COLS = [
            "evapotranspiration_mm",
            "rain_mm",
            "max_temp_c",
            "min_temp_c",
            "max_humidity_pct",
            "min_humidity_pct",
            "avg_wind_speed_mps"
        ]


        # --- date features ---
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

        # --- missingness mask (before split, before fillna) ---
        for col in NUMERIC_COLS:
            df[col + "_mask"] = df[col].notna().astype(int)

        # --- split ---
        df = df.sort_values(["station_id", "date"])
        train_df = df[df["date"] < "2023-01-01"].copy()
        val_df = df[(df["date"] >= "2023-01-01") & (df["date"] < "2025-01-01")].copy()
        test_df = df[df["date"] >= "2025-01-01"].copy()
        if verbose:
            print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

        # --- normalisation (fit on train only) ---
        stats = {}
        for col in NUMERIC_COLS:
            mean = train_df[col].mean()
            std = train_df[col].std()
            stats[col] = {"mean": float(mean), "std": float(std)}
            for split_df in [train_df, val_df, test_df]:
                split_df[col] = (split_df[col] - mean) / (std + 1e-8)

        stats["num_stations"] = int(df["station_id"].nunique())
        stats_path = "transformer_stats.json"

        with open(stats_path, "w") as f:
            json.dump(stats, f, indent=4)
        if verbose:
            print("Saved normalisation stats to transformer_stats.json")
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO model_stats (stats)
                VALUES (%s)
                """,
                (json.dumps(stats),)
            )
        conn.commit()

        # --- lag features ---
        def add_lags(df):
            for col in NUMERIC_COLS:
                for lag in LAG_STEPS:
                    df[f"{col}_lag{lag}"] = df.groupby("station_id")[col].shift(lag)
            return df

        train_df = add_lags(train_df)
        val_df = add_lags(val_df)
        test_df = add_lags(test_df)

        # --- rolling mean features only (no std — correlated with mean) ---
        def add_rolling_stats(df):
            for col in NUMERIC_COLS:
                for window in ROLLING_WINDOWS:
                    df[f"{col}_rmean{window}"] = df.groupby("station_id")[col].transform(
                        lambda x: x.shift(1).rolling(window, min_periods=1).mean()
                    )
            return df

        if verbose:
            print("Adding rolling stats to train ...")
        train_df = add_rolling_stats(train_df)
        if verbose:
            print("Adding rolling stats to val ...")
        val_df = add_rolling_stats(val_df)
        if verbose:
            print("Adding rolling stats to test ...")
        test_df = add_rolling_stats(test_df)

        # --- fill NaN ---
        for split_df in [train_df, val_df, test_df]:
            split_df.fillna(0, inplace=True)

        # --- final feature list ---
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

        if verbose:
            print(f"\nTotal features: {len(FEATURES)}")
            print("Feature breakdown:")
            print(f"  Numeric cols:       {len(NUMERIC_COLS)}")
            print(f"  Mask cols:          {len(mask_cols)}")
            print(f"  Lag cols:           {len(lag_cols)}")
            print(f"  Rolling mean cols:  {len(rolling_mean_cols)}")
            print(f"  Time cols:          {len(time_cols)}")
            print(f"  station_id:         1")
            print(f"  (removed: rolling std cols, availability cols)\n")

        train_df = train_df[FEATURES + ["date"]]
        val_df = val_df[FEATURES + ["date"]]
        test_df = test_df[FEATURES + ["date"]]

        train_df.to_csv(TRAIN_FILE, index=False)
        val_df.to_csv(VAL_FILE, index=False)
        test_df.to_csv(TEST_FILE, index=False)
        if verbose:
            print(f"Saved splits to {TRAIN_FILE}, {VAL_FILE}, {TEST_FILE}")

        conn.close()

    except Exception as e:
        import traceback
        print("Error:", e)
        traceback.print_exc()


if __name__ == "__main__":
    run_prepare_transformer_data()