import numpy as np
import pandas as pd
import json
import os
from pathlib import Path


print("-" * 100)
config_path = Path(__file__).parent.parent / "config.json"

try:
    print("\nPreparing transformer data ...")
    with open(config_path) as f:
        config = json.load(f)

    LAG_STEPS = [1,2,3]
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

    # station_id
    df["station_id"] = df["station_name"].astype("category").cat.codes
    station_mapping = dict(enumerate(df["station_name"].astype("category").cat.categories))
    with open("station_id.txt", "w") as f:
        for key, value in station_mapping.items():
            f.write(f"{key}: {value}\n")

    # date features
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["station_id", "date"])
    df["day_of_year"] = df["date"].dt.dayofyear
    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["sin_day"] = np.sin(2 * np.pi * df["day_of_year"] / 365)
    df["cos_day"] = np.cos(2 * np.pi * df["day_of_year"] / 365)
    df["sin_month"] = np.sin(2 * np.pi * df["month"] / 12)
    df["cos_month"] = np.cos(2 * np.pi * df["month"] / 12)

    # masking for missing values
    for col in NUMERIC_COLS:
        df[col + "_mask"] = df[col].notna().astype(int)

    # availability features
    availability = df.groupby("station_id")[NUMERIC_COLS].apply(lambda x: x.notna().mean())
    availability.columns = [col + "_available" for col in NUMERIC_COLS]
    df = df.merge(availability, on="station_id", how="left")

    # manual normalization
    df = df.sort_values(["station_id", "date"])
    train_df = df[df["date"] < "2023-01-01"].copy()
    val_df = df[(df["date"] >= "2023-01-01") & (df["date"] < "2025-01-01")].copy()
    test_df = df[df["date"] >= "2025-01-01"].copy()
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
    print("Saved normalization stats")
    print("Saved normalization stats to transformer_stats.json")
   
    # lag features
    def add_lags(df):
        for col in NUMERIC_COLS:
            for lag in LAG_STEPS:
                df[f"{col}_lag{lag}"] = df.groupby("station_id")[col].shift(lag)
        return df
    train_df = add_lags(train_df)
    val_df = add_lags(val_df)
    test_df = add_lags(test_df)
    for split_df in [train_df, val_df, test_df]:
        split_df[NUMERIC_COLS] = split_df[NUMERIC_COLS].fillna(0)
        split_df.fillna(0, inplace=True)

    # final feature list
    mask_cols = [col + "_mask" for col in NUMERIC_COLS]
    availability_cols = [col + "_available" for col in NUMERIC_COLS]
    lag_cols = [f"{col}_lag{lag}" for col in NUMERIC_COLS for lag in LAG_STEPS]
    time_cols = ["sin_day", "cos_day", "sin_month", "cos_month", "day_of_week"]
    FEATURES = NUMERIC_COLS + mask_cols + lag_cols + availability_cols + time_cols + ["station_id"]
    train_df = train_df[FEATURES + ["date"]]
    val_df = val_df[FEATURES + ["date"]]
    test_df = test_df[FEATURES + ["date"]]

    train_df.to_csv(TRAIN_FILE, index=False)
    val_df.to_csv(VAL_FILE, index=False)
    test_df.to_csv(TEST_FILE, index=False)
    print(f"Saved train, val, test splits to {TRAIN_FILE}, {VAL_FILE}, {TEST_FILE}")
    os.remove(INPUT_FILE)
    print(f"Deleted input file {INPUT_FILE}\n")

except Exception as e:
    print("Error:", e, "\n")

print("-" * 100)