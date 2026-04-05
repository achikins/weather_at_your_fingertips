import torch
import json
import sys
from pathlib import Path
from torch.utils.data import DataLoader
sys.path.append(str(Path(__file__).parent.parent))
from encoder_decoder.encoder_decoder_transformer import Transformer
from dataset import WeatherDataset
from get_device import get_device


def denormalise(tensor, stats, target_cols):
    out = tensor.clone()
    for i, col in enumerate(target_cols):
        mean = stats[col]['mean']
        std = stats[col]['std']
        out[:, :, i] = out[:, :, i] * std + mean
    return out


def main():
    device = get_device()

    run_number = 1
    run_dir = Path(f"DATA/transformer/encoder_decoder/models/run_{run_number}")
    model_path = run_dir / "model_weights.pt"
    stats_path = Path("DATA/transformer/transformer_stats.json")
    output_file = run_dir / f"output_{run_number}.txt"

    if not model_path.exists() or not stats_path.exists():
        print(f"Model weights or stats not found in {run_dir}. Please run the training script first.")
        return

    config_path = Path(__file__).parent.parent.parent / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    TEST_FILE = config["test_path"]

    test_dataset = WeatherDataset(
        TEST_FILE,
        seq_len=60,
        forecast_horizon=7,
        target_cols=None
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=64,
        shuffle=False,
        num_workers=2,
        pin_memory=False,
        persistent_workers=True
    )

    model = Transformer(
        num_features=len(test_dataset.feature_cols),
        num_stations=495,
        d_model=128,
        nhead=8,
        num_layers=3,
        forecast_horizon=7,
        target_dim=len(test_dataset.target_cols)
    ).to(device)

    checkpoint = torch.load(model_path, map_location=device)   
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    with open(stats_path) as f:
        stats = json.load(f)

    target_cols = test_dataset.target_cols
    try:
        target_indices = test_dataset.target_indices
    except AttributeError:
        raise ValueError(
            "WeatherDataset must have 'target_indices'. "
            "Add: self.target_indices = [self.feature_cols.index(col) for col in self.target_cols]"
        )

    mae_total = 0
    rmse_total = 0
    baseline_mae_total = 0
    horizon_mae = torch.zeros(7).to(device)
    feature_mae = torch.zeros(len(target_cols)).to(device)
    count = 0
    with torch.no_grad():
        for batch_idx, (X, Y, station_id) in enumerate(test_loader):
            X, Y, station_id = X.to(device), Y.to(device), station_id.to(device)
            Y_input = torch.zeros_like(Y)
            Y_input[:, 1:, :] = Y[:, :-1, :]
            Y_input[:, 0, :] = 0
            pred = model(X, station_id, Y_input)
            baseline = X[:, -1, target_indices].unsqueeze(1).repeat(1, 7, 1)
            pred = denormalise(pred, stats, target_cols)
            Y = denormalise(Y, stats, target_cols)
            baseline = denormalise(baseline, stats, target_cols)
            if batch_idx == 0:
                print("\nDEBUG SHAPES:")
                print("pred:", pred.shape)
                print("Y:", Y.shape)
                print("baseline:", baseline.shape)
            mae = torch.mean(torch.abs(pred - Y))
            rmse = torch.sqrt(torch.mean((pred - Y) ** 2))
            baseline_mae = torch.mean(torch.abs(baseline - Y))
            batch_size = X.size(0)
            mae_total += mae.item() * batch_size
            rmse_total += rmse.item() * batch_size
            baseline_mae_total += baseline_mae.item() * batch_size
            horizon_mae += torch.mean(torch.abs(pred - Y), dim=(0, 2)) * batch_size
            feature_mae += torch.mean(torch.abs(pred - Y), dim=(0, 1)) * batch_size
            count += batch_size

    mae_avg = mae_total / count
    rmse_avg = rmse_total / count
    baseline_mae_avg = baseline_mae_total / count
    horizon_mae_avg = horizon_mae / count
    feature_mae_avg = feature_mae / count

    with open(output_file, "w") as f:
        f.write("===== FINAL EVALUATION =====\n")
        f.write(f"MAE: {mae_avg:.4f}\n")
        f.write(f"RMSE: {rmse_avg:.4f}\n")
        f.write(f"Baseline MAE: {baseline_mae_avg:.4f}\n\n")

        f.write("--- MAE by Forecast Horizon ---\n")
        for i, val in enumerate(horizon_mae_avg):
            f.write(f"Day {i+1}: {val.item():.4f}\n")

        f.write("\n--- MAE by Feature ---\n")
        for col, val in zip(target_cols, feature_mae_avg):
            f.write(f"{col}: {val.item():.4f}\n")

        f.write("\n--- Improvement over Baseline ---\n")
        improvement = (baseline_mae_avg - mae_avg) / baseline_mae_avg * 100
        f.write(f"Improvement: {improvement:.4f}%\n")

        f.write("\n================================\n")

    print(f"Evaluation results saved to {output_file}")


if __name__ == "__main__":
    main()