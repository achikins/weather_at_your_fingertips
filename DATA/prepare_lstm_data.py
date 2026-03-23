import numpy as np
import pandas as pd
import json
import os


print("-" * 100)
try:
    print("\nPreparing lstm data ...")
    with open("config.json") as f:
        config = json.load(f)

    INPUT_FILE = config["clean_data_path"]
    OUTPUT_FILE = config["lstm_dataset_path"]
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

    for col in NUMERIC_COLS:
        df[col + "_mask"] = df[col].notna().astype(int)

    df[NUMERIC_COLS] = df[NUMERIC_COLS].fillna(0)

    df["station_id"] = df["station_name"].astype("category").cat.codes
    station_mapping = dict(enumerate(df['station_name'].astype("category").cat.categories))
    with open("station_id.txt", "w") as f:
        for key, value in station_mapping.items():
            f.write(f"{key}: {value}\n")

    df["date"] = pd.to_datetime(df["date"])
    day_of_year = df["date"].dt.dayofyear
    df["sin_day"] = np.sin(2 * np.pi * day_of_year / 365)
    df["cos_day"] = np.cos(2 * np.pi * day_of_year / 365)

    mask_cols = [col + "_mask" for col in NUMERIC_COLS]
    FEATURES = NUMERIC_COLS + mask_cols + ["station_id", "sin_day", "cos_day"]
    df = df[FEATURES + ["date"]]

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Processed dataset saved as {OUTPUT_FILE}")

    os.remove(INPUT_FILE)
    print(f"Deleted input file {INPUT_FILE}\n")


except Exception as e:
    print("Error:", e, "\n")

print("-" * 100)