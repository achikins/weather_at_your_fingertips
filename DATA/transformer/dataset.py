import torch
from torch.utils.data import Dataset
import pandas as pd
import numpy as np


class WeatherDataset(Dataset):
    def __init__(self, csv_file, seq_len=60, forecast_horizon=7, target_cols=None):
        self.df = pd.read_csv(csv_file)
        self.seq_len = seq_len
        self.forecast_horizon = forecast_horizon

        self.target_cols = target_cols or [
            "rain(mm)",
            "maximum_temperature(°C)",
            "minimum_temperature(°C)",
            "maximum_relative_humidity(%)",
            "minimum_relative_humidity(%)",
            "average_10m_wind_speed(m/sec)"
        ]
        self.df = self.df.sort_values(["station_id", "date"])
        self.feature_cols = [col for col in self.df.columns if col not in ["date"]]

        self.data = self.df.values
        self.groups = self.df.groupby("station_id").indices
        self.indices = []

        for station_id, idxs in self.groups.items():
            idxs = sorted(idxs)
            for i in range(len(idxs) - self.seq_len - self.forecast_horizon + 1):
                self.indices.append((idxs[i], station_id))
        
        self.target_indices = [self.feature_cols.index(col) for col in self.target_cols]

    def __len__(self):
        return len(self.indices)
    
    def __getitem__(self, idx):
        start_idx, station_id = self.indices[idx]

        x = self.df.iloc[
            start_idx:
            start_idx + self.seq_len
        ]
        y = self.df.iloc[
            start_idx + self.seq_len:
            start_idx + self.seq_len + self.forecast_horizon
        ]
        X = x[self.feature_cols].values.astype(np.float32)
        Y = y[self.target_cols].values.astype(np.float32)

        station_id = int(x["station_id"].iloc[0])
        return torch.tensor(X), torch.tensor(Y), torch.tensor(station_id)
    

