import torch
import json
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from torch.utils.data import Dataset, DataLoader
sys.path.append(str(Path(__file__).parent.parent))
from encoder_only.encoder_only_transformer import Transformer as EncoderOnlyTransformer
from encoder_decoder.encoder_decoder_transformer import Transformer as EncoderDecoderTransformer
from get_device import get_device


TARGET_COLS = [
    "rain(mm)",
    "maximum_temperature(°C)",
    "minimum_temperature(°C)",
    "maximum_relative_humidity(%)",
    "minimum_relative_humidity(%)",
    "average_10m_wind_speed(m/sec)"
]


class LatestWindowDataset(Dataset):
    def __init__(self, csv_file, seq_len=60):
        self.seq_len = seq_len
        df = pd.read_csv(csv_file)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(["station_id", "date"])

        self.feature_cols = [col for col in df.columns if col != "date"]
        self.target_cols = TARGET_COLS

        self.samples = []
        self.station_names = []

        for station_id, group in df.groupby("station_id"):
            group = group.sort_values("date")
            if len(group) < seq_len:
                print(f"Station {station_id} skipped — only {len(group)} rows (need {seq_len})")
                continue

            window = group.iloc[-seq_len:]
            X = window[self.feature_cols].values.astype(np.float32)
            last_date = window["date"].iloc[-1]

            self.samples.append((
                torch.tensor(X),
                torch.tensor(int(station_id)),
                last_date
            ))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        X, station_id, _ = self.samples[idx]
        return X, station_id

    def get_metadata(self):
        return [(s[1].item(), s[2]) for s in self.samples]
    

def denormalise(array, stats):
    out = array.copy()
    for i, col in enumerate(TARGET_COLS):
        mean = stats[col]["mean"]
        std = stats[col]["std"]
        out[:, i] = out[:, i] * std + mean
    return out


if __name__ == "__main__":
    data_path = Path(__file__).parent / "test.csv"

    dataset = LatestWindowDataset(data_path, seq_len=60)

    rows = []
    feature_cols = dataset.feature_cols
    metadata = dataset.get_metadata()

    for i in range(len(dataset)):
        X, station_id = dataset[i]
        station_id_meta, last_date = metadata[i]

        X_np = X.numpy()

        for t in range(dataset.seq_len):
            row = {
                "station_id": station_id.item(),
                "timestep": t + 1,
                "last_date": last_date
            }

            for f_idx, f_name in enumerate(feature_cols):
                row[f_name] = X_np[t, f_idx]

            rows.append(row)

    df_out = pd.DataFrame(rows)
    df_out.to_csv("transformer/latest_window.csv", index=False)

    print("Saved to latest_window.csv")