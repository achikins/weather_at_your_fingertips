import pandas as pd
import os
import json


def run_clean_data_wo_imputation(verbose=True):
    with open("config.json") as f:
        config = json.load(f)

    INPUT_FILE = config["combined_data_path"]
    OUTPUT_FILE = config["clean_data_path"]

    NUMERIC_COLS = [
        "evapotranspiration(mm)",
        "rain(mm)",
        "maximum_temperature(°C)",
        "minimum_temperature(°C)",
        "maximum_relative_humidity(%)",
        "minimum_relative_humidity(%)",
        "average_10m_wind_speed(m/sec)",
    ]

    df = pd.read_csv(INPUT_FILE, low_memory=False)
    df["date"] = pd.to_datetime(df["date"])

    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if verbose:
        print(f"Loaded {len(df)} rows from {INPUT_FILE}")
        print(f"Missing values BEFORE cleaning:\n{df[NUMERIC_COLS].isna().sum().to_string()}\n")

    cleaned_groups = []

    for station, group in df.groupby("station_name", sort=False):
        group = group.sort_values("date").copy()
        group = group.groupby("date", as_index=False).agg({
            "evapotranspiration(mm)": "mean",
            "rain(mm)": "mean",
            "maximum_temperature(°C)": "mean",
            "minimum_temperature(°C)": "mean",
            "maximum_relative_humidity(%)": "mean",
            "minimum_relative_humidity(%)": "mean",
            "average_10m_wind_speed(m/sec)": "mean",
            "station_name": "first"
        })

        full_dates = pd.date_range(start=group["date"].min(), end=group["date"].max(), freq="D")
        group = group.set_index("date").reindex(full_dates)
        group["station_name"] = station
        for col in NUMERIC_COLS:
            group[col] = group[col].interpolate(
                method="time",
                limit=3,
                limit_direction="both"
            ).round(2)

        group["rain(mm)"] = group["rain(mm)"].clip(lower=0)
        group = group.reset_index().rename(columns={"index": "date"})

        required = [
            "station_name",
            "date",
            "evapotranspiration(mm)",
            "rain(mm)",
            "maximum_temperature(°C)",
            "minimum_temperature(°C)",
            "maximum_relative_humidity(%)",
            "minimum_relative_humidity(%)",
            "average_10m_wind_speed(m/sec)"
        ]
        cleaned_groups.append(group[required])

    cleaned_df = pd.concat(cleaned_groups, ignore_index=True)
    cleaned_df = cleaned_df.sort_values(["station_name", "date"])

    if verbose:
        print(f"Total rows: {len(cleaned_df)}")
        print(f"Missing values AFTER cleaning:\n{cleaned_df[NUMERIC_COLS].isna().sum().to_string()}")
        print("Note: remaining NaNs are long gaps (>3 days) — preserved intentionally.")
        print("Masking in prepare_transformer_data.py handles these as zero-filled placeholders.")

    cleaned_df.to_csv(OUTPUT_FILE, index=False)
    if os.path.exists(INPUT_FILE):
        os.remove(INPUT_FILE)
        if verbose:
            print(f"Deleted input file {INPUT_FILE}")
    if verbose:
        print(f"Saved to {OUTPUT_FILE}\n")
