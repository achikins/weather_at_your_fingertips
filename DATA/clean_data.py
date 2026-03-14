import pandas as pd
import lightgbm
import os


INPUT_FILE = "combine_data.csv"
OUTPUT_FILE = "clean_data.csv"

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

print("-" * 100)
print(f"\nloaded {len(df)} rows from {INPUT_FILE}")
print(f"Total rows: {len(df)}")
print(f"Missing values BEFORE cleaning: \n{df[NUMERIC_COLS].isna().sum().to_string()}\n")

cleaned_groups = []
skipped_info = []

for station, group in df.groupby("station_name", sort=False):

    # interpolation
    group = group.sort_values("date").copy()
    group = group.groupby("date", as_index=False).agg({
        'evapotranspiration(mm)': 'mean',
        'rain(mm)': 'mean',
        'maximum_temperature(°C)': 'mean',
        'minimum_temperature(°C)': 'mean',
        'maximum_relative_humidity(%)': 'mean',
        'minimum_relative_humidity(%)': 'mean',
        'average_10m_wind_speed(m/sec)': 'mean',
        'station_name': 'first'
    })
    full_dates = pd.date_range(start=group["date"].min(), end=group["date"].max(), freq="D")
    group = group.set_index("date").reindex(full_dates)
    group["station_name"] = station
    for col in NUMERIC_COLS:
        group[col] = group[col].interpolate(method="time", limit=3, limit_direction="both").round(2)
    group["rain(mm)"] = group["rain(mm)"].clip(lower=0)
    group = group.reset_index().rename(columns={"index": "date"})

    #imputation
    for col in NUMERIC_COLS:
        for lag in range(1,4):
            group[f"{col}_lag{lag}"] = group[col].shift(lag)
    group["day_of_year"] = group["date"].dt.dayofyear
    group["month"] = group["date"].dt.month
    lag_features = [f"{c}_lag{lag}" for c in NUMERIC_COLS for lag in range(1,4)]
    FEATURES = NUMERIC_COLS + lag_features + ["day_of_year", "month"]
    for target in NUMERIC_COLS:
        missing = group[target].isna()
        if missing.sum() == 0:
            continue
        train_df = group[~missing]
        test_df = group[missing]
        if train_df.empty or test_df.empty:
            skipped_info.append(
                f"Skipping {station} ({target})\n"
                f"Train rows: {len(train_df)}, Test rows: {len(test_df)}\n"
            )
            continue
        x_train = train_df[[c for c in FEATURES if c != target]]
        y_train = train_df[target]
        x_test = test_df[[c for c in FEATURES if c != target]]
        model = lightgbm.LGBMRegressor(
            n_estimators = 50,
            learning_rate = 0.05,
            max_depth = 3,
            random_state = 8989,
            verbose = -1
        )
        model.fit(x_train, y_train)
        prediction = model.predict(x_test)
        group.loc[test_df.index, target] = prediction

    for col in NUMERIC_COLS:
        group[col] = group[col].rolling(window=3, center=True, min_periods=1).mean().round(2)
    group["rain(mm)"] = group["rain(mm)"].clip(lower=0)

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
cleaned_df.sort_values(["station_name", "date"])

print(f"\nTotal rows: {len(cleaned_df)}")
print(f"Missing values AFTER cleaning: \n{cleaned_df[NUMERIC_COLS].isna().sum().to_string()}\n") 

cleaned_df.to_csv(OUTPUT_FILE, index=False)
if os.path.exists(INPUT_FILE):
    os.remove(INPUT_FILE)
    print(f"File {INPUT_FILE} has been deleted")
print(f"File saved to {OUTPUT_FILE}\n")
print("-" * 100)

print(f"\nMissing features:\n")
for x in skipped_info:
    print(x)

print("-" * 100)
