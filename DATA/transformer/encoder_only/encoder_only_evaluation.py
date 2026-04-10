import torch
import json
import sys
from pathlib import Path
from torch.utils.data import DataLoader
sys.path.append(str(Path(__file__).parent.parent))
from encoder_only.encoder_only_transformer import Transformer
from dataset import WeatherDataset
from get_device import get_device


def denormalise(tensor, stats, target_cols):
    out = tensor.clone()
    for i, col in enumerate(target_cols):
        mean = stats[col]['mean']
        std = stats[col]['std']
        out[:, :, i] = out[:, :, i] * std + mean
    return out


def evaluate(model, test_loader, stats, target_cols, device="cpu"):
    mae_total = 0
    rmse_total = 0
    baseline_mae_total = 0

    horizon_mae = torch.zeros(7).to(device)
    feature_mae = torch.zeros(len(target_cols)).to(device)

    count = 0

    with torch.no_grad():
        for X, Y, station_id in test_loader:
            X, Y, station_id = X.to(device), Y.to(device), station_id.to(device)

            # ✅ encoder-only forward
            pred = model(X, station_id)

            # ✅ correct baseline
            target_indices = test_loader.dataset.target_indices
            baseline = X[:, -1, target_indices].unsqueeze(1).repeat(1, 7, 1)

            # --- denormalise ---
            pred = denormalise(pred, stats, target_cols)
            Y = denormalise(Y, stats, target_cols)
            baseline = denormalise(baseline, stats, target_cols)

            # --- metrics ---
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

    # --- averages ---
    mae_avg = mae_total / count
    rmse_avg = rmse_total / count
    baseline_mae_avg = baseline_mae_total / count
    horizon_mae_avg = horizon_mae / count
    feature_mae_avg = feature_mae / count

    # --- pretty output ---
    output_lines = []
    output_lines.append("Encoder-Only Evaluation\n" + "="*40)
    output_lines.append(f"MAE: {mae_avg:.4f}")
    output_lines.append(f"RMSE: {rmse_avg:.4f}")
    output_lines.append(f"Baseline MAE: {baseline_mae_avg:.4f}\n")

    output_lines.append("--- MAE by Forecast Horizon ---")
    for i, val in enumerate(horizon_mae_avg):
        output_lines.append(f"Day {i+1}: {val.item():.4f}")

    output_lines.append("\n--- MAE by Feature ---")
    for col, val in zip(target_cols, feature_mae_avg):
        output_lines.append(f"{col}: {val.item():.4f}")

    improvement = (baseline_mae_avg - mae_avg) / baseline_mae_avg * 100
    output_lines.append("\n--- Improvement over Baseline ---")
    output_lines.append(f"Improvement: {improvement:.2f}%")
    output_lines.append("="*40 + "\n")

    return "\n".join(output_lines)


def main():
    device = get_device()

    # ✅ Use run-based structure (same as encoder-decoder)
    run_number = 2
    run_dir = Path(f"transformer/encoder_only/models/run{run_number}")
    model_path = run_dir / "transformer_model.pt"
    stats_path = Path("transformer/transformer_stats.json")
    output_file = run_dir / f"output_{run_number}.txt"

    # ✅ checks
    if not model_path.exists():
        print(f"Model weights not found in {run_dir}")
        print(model_path)
        return

    if not stats_path.exists():
        print(f"Stats not found in {stats_path}")
        return

    # ✅ correct config path
    config_path = Path(__file__).parent.parent.parent / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    with open(stats_path) as f:
        stats = json.load(f)

    TEST_FILE = config["test_path"]

    # --- dataset ---
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
        num_stations=stats["num_stations"],
        # num_stations=505,
        d_model=128,
        nhead=8,
        num_layers=3,
        forecast_horizon=7,
        target_dim=len(test_dataset.target_cols)
    ).to(device)

    # ✅ load checkpoint (same format as training)
    checkpoint = torch.load(model_path, map_location=device)
    if "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model.load_state_dict(checkpoint)
    model.eval()

    target_cols = test_dataset.target_cols

    # --- evaluate ---
    output = evaluate(model, test_loader, stats, target_cols, device=device)

    # --- save ---
    with open(output_file, "w") as f:
        f.write(output)

    print(f"Evaluation results saved to {output_file}")


if __name__ == "__main__":
    main()