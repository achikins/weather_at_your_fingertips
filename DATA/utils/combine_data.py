import os
import pandas as pd
import json
import shutil
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
config_path = BASE_DIR / "config.json"


def run_combine_data(verbose=True):
    with open(config_path) as f:
        config = json.load(f)

    BASE_PATH = datetime.today().strftime("%Y-%m-%d") + "/tables"
    OUTPUT_PATH = config["combined_data_path"]
    SUMMARY_PATH = config["station_summary_path"]

    summary = pd.read_csv(SUMMARY_PATH)

    valid_stations = summary[summary['issue'] == "No"]["full_path"].tolist()

    all_data = []
    stations_processed = 0

    for station in valid_stations:

        if not os.path.exists(station):
            continue

        for f in os.listdir(station):
            if not f.endswith(".csv"):
                continue

            path = os.path.join(station, f)

            try:
                df = pd.read_csv(path, skiprows=13, header=None, encoding="latin1")
                df.columns = [
                    "station_name",
                    "date",
                    "evapotranspiration(mm)",
                    "rain(mm)",
                    "pan_evaporation(mm)",
                    "maximum_temperature(°C)",
                    "minimum_temperature(°C)",
                    "maximum_relative_humidity(%)",
                    "minimum_relative_humidity(%)",
                    "average_10m_wind_speed(m/sec)",
                    "solar_radiation(MJ/sq m)"
                ]
                df = df[[
                    "station_name",
                    "date",
                    "evapotranspiration(mm)",
                    "rain(mm)",
                    "maximum_temperature(°C)",
                    "minimum_temperature(°C)",
                    "maximum_relative_humidity(%)",
                    "minimum_relative_humidity(%)",
                    "average_10m_wind_speed(m/sec)"
                ]]

                df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y")
                all_data.append(df)

            except Exception as e:
                print("Skipping", path, e)
        stations_processed += 1


    if not all_data:
        print("No data found")
        exit()

    final_df = pd.concat(all_data, ignore_index=True)
    final_df = final_df.sort_values(["station_name", "date"])
    final_df = final_df[final_df["station_name"] != "Totals:"]
    final_df["station_name"] = final_df["station_name"].astype("category")
    final_df["station_id"] = final_df["station_name"].cat.codes
    station_mapping = dict(enumerate(final_df["station_name"].cat.categories))
    with open("station_id.txt", "w") as f:
        for key, value in station_mapping.items():
            f.write(f"{key}: {value}\n")

    final_df.to_csv(OUTPUT_PATH, index=False)

    if verbose:
        print("Data combination complete")
        print(f"Combined data saved to {OUTPUT_PATH}")
        print(f"Total stations combined: {stations_processed}")
        print(f"Total rows of data: {len(final_df)}")

    parent_folder = os.path.dirname(BASE_PATH)
    if os.path.exists(parent_folder):
        try:
            shutil.rmtree(parent_folder)
            if verbose:
                print(f"Deleted folder {parent_folder}\n")
        except Exception as e:
            print(f"Failed: {e}\n", e)


if __name__ == "__main__":
    run_combine_data()
