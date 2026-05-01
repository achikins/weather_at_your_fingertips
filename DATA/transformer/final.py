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
from latest_window_dataset import LatestWindowDataset, TARGET_COLS, denormalise
from predict import load_encoder_only, load_encoder_decoder, predict_encoder_only, predict_encoder_decoder, load_station_mapping


def main():
    device = get_device()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        choices=["encoder_only", "encoder_decoder"],
        required=True
    )
    parser.add_argument(
        "--run",
        required=True
    )
    args = parser.parse_args()
    
    station_path = Path(__file__).parent.parent / "station_id.txt"
    station_map = load_station_mapping(station_path)
    if args.model == "encoder_only":
        stats_path = Path(__file__).parent / "transformer_stats2.json"
    else:
        stats_path = Path(__file__).parent / "transformer_stats1.json"
    with open(stats_path) as f:
        stats = json.load(f)

    DATA_PATH = Path(__file__).parent / "test.csv"
    dataset = LatestWindowDataset(DATA_PATH, seq_len=60)
    loader = DataLoader(dataset, batch_size=64, shuffle=False, num_workers=2)
    metadata = dataset.get_metadata()
    num_features = len(dataset.feature_cols)
    print(f"Found {len(dataset)} stations with sufficient history\n")

    if args.model == "encoder_only":
        model_path = Path(f"transformer/encoder_only/models/run{args.run}/transformer_model.pt")
        model = load_encoder_only(stats, num_features, device, model_path)
        preds = predict_encoder_only(model, loader, device)
    else:
        model_path = Path(f"transformer/encoder_decoder/models/run{args.run}/transformer_model.pt")
        model = load_encoder_decoder(stats, num_features, device, model_path)
        preds = predict_encoder_decoder(model, loader, device)

    rows = []
    for i, (station_id, last_date) in enumerate(metadata):
        pred_denorm = denormalise(preds[i], stats)
        for day in range(7):
            forecast_date = last_date + pd.Timedelta(days=day + 1)
            row = {
                "station_id": station_id,
                "station_name": station_map.get(station_id, "Unknown"),
                "last_known_date": last_date.date(),
                "forecast_date": forecast_date.date(),
                "forecast_day": day + 1,
            }
            for j, col in enumerate(TARGET_COLS):
                row[col] = round(float(pred_denorm[day, j]), 4)
            rows.append(row)

    out_df = pd.DataFrame(rows)
    model_tag = args.model
    out_path = Path(f"predictions_{model_tag}.csv")
    out_df.to_csv(out_path, index=False)
    print(f"\nPredictions saved to {out_path}")
    print(f"Shape: {out_df.shape} ({len(metadata)} stations x 7 days)")


if __name__ == "__main__":
    main()