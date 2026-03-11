import os
import pandas as pd
import json

with open("config.json") as f:
    config = json.load(f)

BASE_PATH = config["base_path"]
SUMMARY_FILE = "station_summary.csv"

summary = pd.read_csv(SUMMARY_FILE)

valid_stations = summary[summary['issue'] == "No"]["full_path"].tolist()

all_data = []

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
                "station name",
                "date",
                "evapotranspiration(mm)",
                "rain(mm)",
                "pan evaporation(mm)",
                "maximum temperature(°C)",
                "minimum temperature(°C)",
                "maximum relative humidity(%)",
                "minimum relative humidity(%)",
                "average 10m wind speed(m/sec)",
                "solar radiation(MJ/sq m)"
            ]
            df = df[[
                "station name",
                "date",
                "evapotranspiration(mm)",
                "rain(mm)",
                "maximum temperature(°C)",
                "minimum temperature(°C)",
                "maximum relative humidity(%)",
                "minimum relative humidity(%)",
                "average 10m wind speed(m/sec)"
            ]]

            df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y")
            all_data.append(df)

        except Exception as e:
            print("Skipping", path, e)


if not all_data:
    print("No data found")
    exit()

final_df = pd.concat(all_data, ignore_index=True)
final_df = final_df.sort_values(["station name", "date"])
final_df.to_csv("combine_data.csv", index=False)
print("Done")
