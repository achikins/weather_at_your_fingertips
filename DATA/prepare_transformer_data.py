import numpy as np
import pandas as pd
import json
import os   

print("-" * 100)

try:
    print("\nPreparing transformer data ...")
    with open("config.json") as f:
        config = json.load(f)

    LAG_STEPS = [1,2,3]
    INPUT_FILE = config["clean_data_path"]
    OUTPUT_FILE = config["transformer_dataset_path"]

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
    stats = {}
    for col in NUMERIC_COLS:
        mean = df[col].mean()
        std = df[col].std()
        stats[col] = {"mean": float(mean), "std": float(std)}
        df[col] = (df[col] - mean) / (std + 1e-8)
    with open("transformer_stats.json", "w") as f:
        json.dump(stats, f, indent=4)
    print("Saved normalization stats to transformer_stats.json")
   
    # lag features
    df[NUMERIC_COLS].fillna(0)
    for col in NUMERIC_COLS:
        for lag in LAG_STEPS:
            df[f"{col}_lag{lag}"] = df.groupby("station_id")[col].shift(lag)
    df.fillna(0)

    # final feature list
    mask_cols = [col + "_mask" for col in NUMERIC_COLS]
    availability_cols = [col + "_available" for col in NUMERIC_COLS]
    lag_cols = [f"{col}_lag{lag}" for col in NUMERIC_COLS for lag in LAG_STEPS]
    time_cols = ["sin_day", "cos_day", "sin_month", "cos_month", "day_of_week"]
    FEATURES = NUMERIC_COLS + mask_cols + lag_cols + availability_cols + time_cols + ["station_id"]
    df = df[FEATURES + ["date"]]

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Transformer dataset saved as {OUTPUT_FILE}")
    os.remove(INPUT_FILE)
    print(f"Deleted input file {INPUT_FILE}\n")

except Exception as e:
    print("Error:", e, "\n")

print("-" * 100)