import os
import re
import pandas as pd
import json
from datetime import datetime


with open("config.json") as f:
    config = json.load(f)

BASE_PATH = config["base_path"]

MIN_MONTHS = 60
MIN_COVERAGE = 80

rows = []

for root, dirs, files in os.walk(BASE_PATH):
    csv_files = [f for f in files if f.endswith(".csv")]
    if not csv_files:
        continue

    station = os.path.basename(root)
    months = []

    for f in csv_files:
        match = re.search(r"-(\d{6})\.csv$", f)
        if match:
            month_str = match.group(1)
            month_date = datetime.strptime(month_str, "%Y%m")
            months.append(month_date)

    if not months:
        continue

    months = sorted(months)
    start = months[0]
    end = months[-1]
    months_available = len(months)
    total_month = (end.year - start.year) * 12 + (end.month - start.month) + 1
    missing_months = total_month - months_available
    largest_gap = 0
    coverage = months_available / total_month * 100

    for i in range(1, len(months)):
        prev = months[i-1]
        curr = months[i]
        diff = (curr.year - prev.year) * 12 + (curr.month - prev.month) - 1
        if diff > largest_gap:
            largest_gap = diff

    issue = "No"
    today = datetime.today()

    if end.month != today.month:
        issue = "Station Stopped"
    elif months_available < MIN_MONTHS:
        issue = "Not enough data"
    elif coverage < MIN_COVERAGE:
        issue = "Coverage"

    rows.append({
        "station": station,
        "full_path": root,
        "start_month": start.strftime("%Y-%m"),
        "end_month": end.strftime("%Y-%m"),
        "total_months": total_month,
        "months_available": months_available,
        "coverage": coverage,
        "missing_months": missing_months,
        "largest_gap": largest_gap,
        "issue": issue
    })

df = pd.DataFrame(rows)
df = df.sort_values(by="months_available", ascending=False)
df.to_csv("station_summary.csv", index=False)

print("-" * 100)
print(f"\nTotal stations found: {len(df)}")
print(f"\tStations without issues: {sum(df.issue=="No")}")
print(f"\tStations stopped working: {sum(df.issue=="Station Stopped")}")
print(f"\tStations not having enough data: {sum(df.issue=="Not enough data")}")
print(f"\tStations with coverage issue: {sum(df.issue=="Coverage")}")
print("\nStation Summary saved to station_summary.csv\n")
print("-" * 100)
