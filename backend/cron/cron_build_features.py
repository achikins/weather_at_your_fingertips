import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader


TARGET_COLS = [
    "rain_mm",
    "max_temp_c",
    "min_temp_c",
    "max_humidity_pct",
    "min_humidity_pct",
    "avg_wind_speed_mps"
]
NUMERIC_COLS = [
    "evapotranspiration_mm",
    "rain_mm",
    "max_temp_c",
    "min_temp_c",
    "max_humidity_pct",
    "min_humidity_pct",
    "avg_wind_speed_mps"
]
LAG_STEPS = [1, 2, 3, 7]
ROLLING_WINDOWS = [7, 14, 30]


def build_features(df, stats):
    df = df.copy()

    # --- date ---
    df["date"] = pd.to_datetime(df["obs_date"])
    df = df.sort_values(["station_id", "date"])

    df["day_of_year"] = df["date"].dt.dayofyear
    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month

    df["sin_day"] = np.sin(2 * np.pi * df["day_of_year"] / 365)
    df["cos_day"] = np.cos(2 * np.pi * df["day_of_year"] / 365)
    df["sin_month"] = np.sin(2 * np.pi * df["month"] / 12)
    df["cos_month"] = np.cos(2 * np.pi * df["month"] / 12)
    df["season"] = ((df["month"] % 12) // 3).astype(int)

    # --- masks ---
    for col in NUMERIC_COLS:
        df[col + "_mask"] = df[col].notna().astype(int)

    # --- normalization (IMPORTANT: use training stats only) ---
    for col in NUMERIC_COLS:
        mean = stats[col]["mean"]
        std = stats[col]["std"]
        df[col] = (df[col] - mean) / (std + 1e-8)

    # --- lag features ---
    for col in NUMERIC_COLS:
        for lag in LAG_STEPS:
            df[f"{col}_lag{lag}"] = df.groupby("station_id")[col].shift(lag)

    # --- rolling features ---
    for col in NUMERIC_COLS:
        for window in ROLLING_WINDOWS:
            df[f"{col}_rmean{window}"] = df.groupby("station_id")[col].transform(
                lambda x: x.shift(1).rolling(window, min_periods=1).mean()
            )

    # --- fill missing ---
    df.fillna(0, inplace=True)

    # --- feature list (must match training) ---
    mask_cols = [col + "_mask" for col in NUMERIC_COLS]
    lag_cols = [f"{c}_lag{l}" for c in NUMERIC_COLS for l in LAG_STEPS]
    rolling_cols = [f"{c}_rmean{w}" for c in NUMERIC_COLS for w in ROLLING_WINDOWS]
    time_cols = ["sin_day", "cos_day", "sin_month", "cos_month", "day_of_week", "season"]

    FEATURES = (
        NUMERIC_COLS +
        mask_cols +
        lag_cols +
        rolling_cols +
        time_cols +
        ["station_id"]
    )

    return df[FEATURES + ["date"]]

class WindowDataset(Dataset):
    def __init__(self, feature_df, seq_len=60):
        self.samples = []
        self.metadata = []   # (station_id, last_date)

        # feature_cols = everything except 'date'
        self.feature_cols = [c for c in feature_df.columns if c != "date"]

        for station_id, group in feature_df.groupby("station_id"):
            group = group.sort_values("date")
            if len(group) < seq_len:
                print(f"  Skipping station {station_id} — only {len(group)} rows")
                continue

            window = group.iloc[-seq_len:]
            X = window[self.feature_cols].values.astype(np.float32)
            last_date = window["date"].iloc[-1]

            self.samples.append((
                torch.tensor(X),
                torch.tensor(int(station_id))
            ))
            self.metadata.append((int(station_id), last_date))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]


def denormalise(array, stats):
    """array shape: (7, len(TARGET_COLS))"""
    out = array.copy()
    for i, col in enumerate(TARGET_COLS):
        out[:, i] = out[:, i] * stats[col]["std"] + stats[col]["mean"]
    return out
