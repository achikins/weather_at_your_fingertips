import pandas as pd
import json
from pathlib import Path


with open("config.json") as f:
    config = json.load(f)

INPUT_FILE = config["combined_data_path"]

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

total_rows = len(df)
print("=" * 80)
print(f"LOADED: {total_rows:,} rows, {df['station_name'].nunique()} stations")
print("=" * 80)

# ===== STAGE 1: INITIAL MISSINGNESS =====
print("\n--- STAGE 1: Initial missingness (raw data) ---")
stage1 = df[NUMERIC_COLS].isna()
for col in NUMERIC_COLS:
    n = stage1[col].sum()
    pct = n / total_rows * 100
    print(f"  {col:<45} {n:>8,} missing  ({pct:>6.2f}%)")
print(f"  {'TOTAL (any column missing)':<45} {stage1.any(axis=1).sum():>8,} rows    ({stage1.any(axis=1).sum() / total_rows * 100:>6.2f}%)")

# ===== STAGE 2: AFTER DEDUPLICATION + DATE REINDEX =====
print("\n--- STAGE 2: After deduplication + reindexing missing dates ---")
groups = []
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
    group = group.reset_index().rename(columns={"index": "date"})
    groups.append(group)

df2 = pd.concat(groups, ignore_index=True)
total_rows2 = len(df2)
stage2 = df2[NUMERIC_COLS].isna()
print(f"  Total rows after reindex: {total_rows2:,} (added {total_rows2 - total_rows:,} date gap rows)")
for col in NUMERIC_COLS:
    n = stage2[col].sum()
    pct = n / total_rows2 * 100
    print(f"  {col:<45} {n:>8,} missing  ({pct:>6.2f}%)")
print(f"  {'TOTAL (any column missing)':<45} {stage2.any(axis=1).sum():>8,} rows    ({stage2.any(axis=1).sum() / total_rows2 * 100:>6.2f}%)")

# ===== STAGE 3: AFTER INTERPOLATION (limit=3) =====
print("\n--- STAGE 3: After interpolation (limit=3 days) ---")
groups3 = []
for station, group in df2.groupby("station_name", sort=False):
    group = group.copy().set_index("date")  # ← set date as index for time interpolation
    for col in NUMERIC_COLS:
        group[col] = group[col].interpolate(method="time", limit=3, limit_direction="both").round(2)
    group["rain(mm)"] = group["rain(mm)"].clip(lower=0)
    group = group.reset_index()             # ← restore date as column
    groups3.append(group)

df3 = pd.concat(groups3, ignore_index=True)
stage3 = df3[NUMERIC_COLS].isna()
for col in NUMERIC_COLS:
    n = stage3[col].sum()
    pct = n / total_rows2 * 100
    filled = stage2[col].sum() - n
    print(f"  {col:<45} {n:>8,} missing  ({pct:>6.2f}%)  [{filled:,} filled by interpolation]")
print(f"  {'TOTAL (any column missing)':<45} {stage3.any(axis=1).sum():>8,} rows    ({stage3.any(axis=1).sum() / total_rows2 * 100:>6.2f}%)")

# ===== GAP LENGTH ANALYSIS =====
print("\n--- GAP length distribution (remaining after interpolation) ---")
print("  (these are the gaps >3 days that will become zeros + mask=0)\n")
for col in NUMERIC_COLS:
    gap_lengths = []
    for station, group in df3.groupby("station_name", sort=False):
        series = group[col].isna().astype(int)
        # find consecutive runs of NaN
        gap = 0
        for val in series:
            if val == 1:
                gap += 1
            else:
                if gap > 0:
                    gap_lengths.append(gap)
                gap = 0
        if gap > 0:
            gap_lengths.append(gap)

    if gap_lengths:
        s = pd.Series(gap_lengths)
        print(f"  {col}:")
        print(f"    Gaps >3 days:   {len(s):,}")
        print(f"    Median gap:     {s.median():.0f} days")
        print(f"    Mean gap:       {s.mean():.1f} days")
        print(f"    Max gap:        {s.max():.0f} days")
        print(f"    >30 day gaps:   {(s > 30).sum():,}")
        print(f"    >90 day gaps:   {(s > 90).sum():,}")
    else:
        print(f"  {col}: no remaining gaps")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"  Raw missing:              {stage1.any(axis=1).sum() / total_rows * 100:.2f}%")
print(f"  After reindex missing:    {stage2.any(axis=1).sum() / total_rows2 * 100:.2f}%")
print(f"  After interpolation:      {stage3.any(axis=1).sum() / total_rows2 * 100:.2f}%")
print(f"  Remaining (→ zeros):      {stage3.any(axis=1).sum():,} rows")
print("=" * 80)