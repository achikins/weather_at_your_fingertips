import os
import pandas as pd
import json
import shutil


print("-" * 100)
print("\nCombining data ...")
with open("config.json") as f:
    config = json.load(f)

BASE_PATH = config["base_path"]
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
final_df.to_csv(OUTPUT_PATH, index=False)

print("\nData combination complete")
print(f"Combined data saved to {OUTPUT_PATH}\n")
print(f"Total stations combined: {stations_processed}")
print(f"Total rows of data: {len(final_df)}\n")

parent_folder = os.path.dirname(BASE_PATH)
if os.path.exists(parent_folder):
    try:
        shutil.rmtree(parent_folder)
        print(f"Deleted folder {parent_folder}\n")
    except Exception as e:
        print(f"Failed: {e}\n", e)

print("-" * 100)
