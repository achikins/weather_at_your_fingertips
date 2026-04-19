import torch
import json
import sys
import argparse
import pandas as pd
import re
import numpy as np
from pathlib import Path
from torch.utils.data import Dataset, DataLoader
sys.path.append(str(Path(__file__).parent.parent))
from encoder_only.encoder_only_transformer import Transformer as EncoderOnlyTransformer
from encoder_decoder.encoder_decoder_transformer import Transformer as EncoderDecoderTransformer
from get_device import get_device
from latest_window_dataset import LatestWindowDataset, TARGET_COLS, denormalise


def load_encoder_only(stats, num_features, device, model_path):
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    model = EncoderOnlyTransformer(
        num_features=num_features,
        num_stations=stats["num_stations"],
        d_model=128,
        nhead=8,
        num_layers=3,
        forecast_horizon=7,
        target_dim=len(TARGET_COLS)
    ).to(device)

    checkpoint = torch.load(model_path, map_location=device)
    if "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model.load_state_dict(checkpoint)

    print(f"Loaded encoder-only model from {model_path}")
    return model


def load_encoder_decoder(stats, num_features, device, model_path):
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    model = EncoderDecoderTransformer(
        num_features=num_features,
        num_stations=stats["num_stations"],
        d_model=128,
        nhead=8,
        num_layers=3,
        forecast_horizon=7,
        target_dim=len(TARGET_COLS)
    ).to(device)

    checkpoint = torch.load(model_path, map_location=device)
    if "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model.load_state_dict(checkpoint)

    print(f"Loaded encoder-decoder model from {model_path}")
    return model


def predict_encoder_only(model, loader, device):
    model.eval()
    all_preds = []
    with torch.no_grad():
        for X, station_id in loader:
            X, station_id = X.to(device), station_id.to(device)
            pred = model(X, station_id)
            all_preds.append(pred.cpu().numpy())
    return np.concatenate(all_preds, axis=0)


def predict_encoder_decoder(model, loader, device):
    model.eval()
    all_preds = []
    with torch.no_grad():
        for X, station_id in loader:
            X, station_id = X.to(device), station_id.to(device)
            batch_size = X.size(0)

            decoder_input = torch.zeros(batch_size, 1, len(TARGET_COLS)).to(device)
            preds = []
            for t in range(7):
                out = model(X, station_id, decoder_input)
                next_pred = out[:, -1:, :]
                preds.append(next_pred)
                decoder_input = torch.cat([decoder_input, next_pred], dim=1)

            pred = torch.cat(preds, dim=1)
            all_preds.append(pred.cpu().numpy())
    return np.concatenate(all_preds, axis=0)


def load_station_mapping(station_id_path):
    station_map = {}
    with open(station_id_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            match = re.match(r"(\d+):\s*(.*)", line)
            if match:
                station_id = int(match.group(1))
                station_name = match.group(2)
                station_map[station_id] = station_name
    return station_map
