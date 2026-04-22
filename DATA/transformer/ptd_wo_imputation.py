import numpy as np
import pandas as pd
import json
import os
from pathlib import Path


def run_prepare_transformer_data_wo_imputation(verbose=True):
    config_path = Path(__file__).parent.parent / "config.json"
    try:
        with open(config_path) as f:
            config = json.load(f)

        LAG_STEPS = [1, 2, 3, 7]
        ROLLING_WINDOWS = [7, 14, 30]
        INPUT_FILE = config["clean_data_path"]
        TRAIN_FILE = config["train_path"]
        VAL_FILE = config["val_path"]
        TEST_FILE = config["test_path"]

        df = pd.read_csv(INPUT_FILE)

        NUMERIC_COLS = [
            "evapotranspiration(mm)",
            "rain(mm)",
            "maximum_temperature(°C)",
            "minimum_temperature(°C)",
            "maximum_relative_humidity(%)",
            "minimum_relative_humidity(%)",
            "average_10m_wind_speed(m/sec)"
        ]

        df["station_id"] = df["station_name"].astype("category").cat.codes
        station_mapping = dict(enumerate(df["station_name"].astype("category").cat.categories))
        with open("station_id.txt", "w") as f:
            for key, value in station_mapping.items():
                f.write(f"{key}: {value}\n")

        df["date"] = pd.to_datetime(df["date"])
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

        availability = df.groupby("station_id")[NUMERIC_COLS].apply(lambda x: x.notna().mean())
        availability.columns = [col + "_available" for col in NUMERIC_COLS]
        df = df.merge(availability, on="station_id", how="left")

        df = df.sort_values(["station_id", "date"])
        train_df = df[df["date"] < "2023-01-01"].copy()
        val_df = df[(df["date"] >= "2023-01-01") & (df["date"] < "2025-01-01")].copy()
        test_df = df[df["date"] >= "2025-01-01"].copy()
        if verbose:
           print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

        stats = {}
        for col in NUMERIC_COLS:
            mean = train_df[col].mean()
            std = train_df[col].std()
            stats[col] = {"mean": float(mean), "std": float(std)}
            for split_df in [train_df, val_df, test_df]:
                split_df[col] = (split_df[col] - mean) / (std + 1e-8)
        stats["num_stations"] = int(df["station_id"].nunique())
        stats_path = Path(__file__).parent / "transformer_stats.json"
        with open(stats_path, "w") as f:
            json.dump(stats, f, indent=4)
        if verbose:
           print("Saved normalisation stats to transformer_stats.json")

        def add_lags(df):
            for col in NUMERIC_COLS:
                for lag in LAG_STEPS:
                    df[f"{col}_lag{lag}"] = df.groupby("station_id")[col].shift(lag)
            return df

        train_df = add_lags(train_df)
        val_df = add_lags(val_df)
        test_df = add_lags(test_df)

        def add_rolling_stats(df):
            for col in NUMERIC_COLS:
                for window in ROLLING_WINDOWS:
                    rolled = df.groupby("station_id")[col].transform(
                        lambda x: x.shift(1).rolling(window, min_periods=1).mean()
                    )
                    df[f"{col}_rmean{window}"] = rolled
                    rolled_std = df.groupby("station_id")[col].transform(
                        lambda x: x.shift(1).rolling(window, min_periods=1).std()
                    )
                    df[f"{col}_rstd{window}"] = rolled_std
            return df

        train_df = add_rolling_stats(train_df)
        val_df = add_rolling_stats(val_df)
        test_df = add_rolling_stats(test_df)

        for split_df in [train_df, val_df, test_df]:
            split_df.fillna(0, inplace=True)

        mask_cols = [col + "_mask" for col in NUMERIC_COLS]
        availability_cols = [col + "_available" for col in NUMERIC_COLS]
        lag_cols = [f"{col}_lag{lag}" for col in NUMERIC_COLS for lag in LAG_STEPS]
        rolling_mean_cols = [f"{col}_rmean{w}" for col in NUMERIC_COLS for w in ROLLING_WINDOWS]
        rolling_std_cols = [f"{col}_rstd{w}" for col in NUMERIC_COLS for w in ROLLING_WINDOWS]
        time_cols = ["sin_day", "cos_day", "sin_month", "cos_month", "day_of_week", "season"]

        FEATURES = (
            NUMERIC_COLS
            + mask_cols
            + lag_cols
            + rolling_mean_cols
            + rolling_std_cols
            + availability_cols
            + time_cols
            + ["station_id"]
        )

        if verbose:
            print(f"Total features: {len(FEATURES)}")
            print("Feature breakdown:")
            print(f"  Numeric cols:       {len(NUMERIC_COLS)}")
            print(f"  Mask cols:          {len(mask_cols)}")
            print(f"  Lag cols:           {len(lag_cols)}")
            print(f"  Rolling mean cols:  {len(rolling_mean_cols)}")
            print(f"  Rolling std cols:   {len(rolling_std_cols)}")
            print(f"  Availability cols:  {len(availability_cols)}")
            print(f"  Time cols:          {len(time_cols)}")
            print(f"  station_id:         1\n")

        train_df = train_df[FEATURES + ["date"]]
        val_df = val_df[FEATURES + ["date"]]
        test_df = test_df[FEATURES + ["date"]]

        train_df.to_csv(TRAIN_FILE, index=False)
        val_df.to_csv(VAL_FILE, index=False)
        test_df.to_csv(TEST_FILE, index=False)
        if verbose:
            print(f"Saved splits to {TRAIN_FILE}, {VAL_FILE}, {TEST_FILE}")

        os.remove(INPUT_FILE)
        if verbose:
            print(f"Deleted input file {INPUT_FILE}\n")

    except Exception as e:
        import traceback
        print("Error:", e)
        traceback.print_exc()
        print()
