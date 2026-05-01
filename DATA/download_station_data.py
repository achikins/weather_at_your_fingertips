from ftplib import FTP
import pandas as pd
import re
import zipfile
import os
import json


def run_download_station_data():
    def clean_station_name(name):
        # remove AWS suffix if present
        name = re.sub(r"\s+AWS(?=\)|$)", "", name)
        name = re.sub(r"\bAWS\b", "", name)
        # replace slashes with underscores
        name = name.replace("/", "_")
        # collapse multiple spaces into one
        name = re.sub(r"\s+", " ", name)
        return name

    def normalize_station_name(name):
        name = name.lower()
        name = re.sub(r"\s+", "_", name)
        return name

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

    with open(CONFIG_PATH) as f:
        config = json.load(f)

    FTP_DIR = "/anon2/home/ncc/metadata/sitelists"
    ZIP_FILENAME = "stations.zip"
    TXT_FILENAME = "stations.txt"
    manual_map = {
        "BRADSHAW": "BRADSHAW HOMESTEAD",
        "CAPE GRIM BAPS (COMPARISON)": "CAPE GRIM BAPS (COMPARISON)",
        "DINNER PLAIN (MOUNT HOTHAM AIRPORT)": "MOUNT HOTHAM",
        "GOOSEBERRY HILL": "MAIDA VALE",
        "HALLS CREEK AIRPORT": "HALLS CREEK AIRPORT (AUTO EVAP)",
        "MACKAY MO": "MACKAY M.O",
        "SALMON GUMS RESSTN": "SALMON GUMS RES.STN.",
        "THEVENARD ISLAND": "THEVENARD ISLAND",
        "WEST ROEBUCK": "ROEBUCK PLAINS"
    }
    stations = []

    if not os.path.exists(TXT_FILENAME):
        print(f"{TXT_FILENAME} not found. Downloading from BOM...")

        ftp = FTP(config["ftp_host"])
        ftp.set_pasv(True)
        ftp.login()
        ftp.cwd(FTP_DIR)

        with open(ZIP_FILENAME, "wb") as f:
            ftp.retrbinary(f"RETR {ZIP_FILENAME}", f.write)

        ftp.quit()
        print(f"Downloaded {ZIP_FILENAME}")

        with zipfile.ZipFile(ZIP_FILENAME, "r") as zip_ref:
            zip_ref.extract(TXT_FILENAME, ".")

        print(f"Extracted {TXT_FILENAME}")
        os.remove(ZIP_FILENAME)

    else:
        print(f"{TXT_FILENAME} already exists. Skipping download.")

    with open(TXT_FILENAME, "r") as f:
        lines = f.readlines()
    start_index = 0
    for i, line in enumerate(lines):
        if line.startswith("-------"):
            start_index = i + 1  # data starts on the next line
            break
    data_lines = lines[start_index:]

    for line in data_lines:
        if len(line.strip()) == 0:  # skip blank lines
            continue
        if not re.match(r"^\d{6}", line.strip()):
            break  # stop at footer

        station_name = line[14:56].strip()
        start = line[56:63].strip()
        end = line[63:71].strip()
        lat = line[71:81].strip()
        lon = line[81:90].strip()
        state = line[105:110].strip()
        elevation = line[110:120].strip()
        
        stations.append({
            "station_name": station_name,
            "start": start,
            "end": end,
            "latitude": lat,
            "longitude": lon,
            "state": state,
            "elevation_m": elevation
        })

    stations_df = pd.DataFrame(stations)
    stations_df["station_name"] = stations_df["station_name"].apply(clean_station_name)
    active_stations_df = stations_df[stations_df["end"] == ".."].copy()

    with open(config["station_id_path"]) as f:
        your_stations = []
        for line in f:
            line = line.strip()
            if not line:
                continue
            station_name = re.sub(r"^\d+:\s*", "", line)
            your_stations.append(station_name)

    your_df = pd.DataFrame({
        "id": range(len(your_stations)),
        "station_name": your_stations
    })

    # keep only the row with the maximum elevation per station name
    stations_max_elev = active_stations_df.copy()
    stations_max_elev = stations_max_elev.sort_values('elevation_m', ascending=False)
    stations_max_elev = stations_max_elev.drop_duplicates(subset='station_name', keep='first')

    merged = pd.merge(
        your_df,
        stations_max_elev,
        on="station_name",
        how="left",
        sort=False
    )

    # keep only the row with the minimum elevation per station name
    stations_min_elev = stations_df.copy()
    stations_min_elev = stations_min_elev.sort_values('elevation_m', ascending=True)
    stations_min_elev = stations_min_elev.drop_duplicates(subset='station_name', keep='first')

    failed_idx = merged[merged["latitude"].isna()].index

    for idx in failed_idx:
        original_name = merged.loc[idx, "station_name"]
        
        # get mapped name (fallback to original if not in map)
        mapped_name = manual_map.get(original_name, original_name)
        
        # find matching row in stations_min_elev
        match = stations_min_elev[stations_min_elev["station_name"] == mapped_name]
        
        if not match.empty:
            row = match.iloc[0]
            
            for col in ["start", "end", "latitude", "longitude", "state", "elevation_m"]:
                merged.loc[idx, col] = row[col]


    # check for rows with missing lat/lon (unsuccessful match)
    failed_merges = merged[merged["latitude"].isna() | merged["longitude"].isna() | merged["elevation_m"].isna()]

    # print each failed row
    for idx, row in failed_merges.iterrows():
        print(f"{idx}: {row['station_name']}")

    # print total number of failed merges
    print(f"Total number of unsuccessful merges: {len(failed_merges)}")

    if not os.path.exists(config["station_summary_path"]):
        print(f"Error: {config["station_summary_path"]} not found.")
        exit(1)
    summary_df = pd.read_csv("station_summary.csv")
    summary_df = summary_df[summary_df["issue"] == "No"].copy()

    merged["station_key"] = merged["station_name"].apply(normalize_station_name)
    summary_df["station_key"] = summary_df["station"].apply(normalize_station_name)

    summary_df["start_month"] = pd.to_datetime(summary_df["start_month"], format="%Y-%m")
    summary_df["end_month"] = pd.to_datetime(summary_df["end_month"], format="%Y-%m")

    merged = pd.merge(
        merged,
        summary_df[["station_key", "start_month", "end_month", "coverage"]],
        on="station_key",
        how="left"
    )

    merged = merged.rename(columns={
        "start_month": "start_date",
        "end_month": "end_date",
        "coverage": "coverage_pct"
    })

    merged = merged.drop(columns=["station_key", "start", "end"])

    merged.to_csv(config["station_dataset_path"], index=False)

    print(f"Station data saved to {config["station_dataset_path"]}")