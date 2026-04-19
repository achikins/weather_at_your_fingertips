import time
import sys
import torch
import torch.nn as nn
import torch.optim as optim
import json
from pathlib import Path
from torch.utils.data import DataLoader
sys.path.append(str(Path(__file__).parent.parent))
from dataset import WeatherDataset
from encoder_decoder.encoder_decoder_transformer import Transformer
from get_device import get_device


def scheduled_sampling_forward(model, X, Y, station_id, tf_ratio, device):
    batch_size, horizon, target_dim = Y.shape
    decoder_input = torch.zeros(batch_size, 1, target_dim).to(device)
    predictions = []
    for t in range(horizon):
        pred = model(X, station_id, decoder_input)
        next_pred = pred[:, -1:, :]
        predictions.append(next_pred)
        if t < horizon - 1:
            use_gt = torch.rand(1).item() < tf_ratio
            next_input = Y[:, t:t+1, :] if use_gt else next_pred.detach()
            decoder_input = torch.cat([decoder_input, next_input], dim=1)
    return torch.cat(predictions, dim=1)


def main():
    config_path = Path(__file__).parent.parent.parent / "config.json"
    stats_path = Path(__file__).parent.parent / "transformer_stats.json"
    device = get_device()

    with open(config_path) as f:
        config = json.load(f)
    with open(stats_path) as f:
        stats = json.load(f)

    TRAIN_FILE = config["train_path"]
    VAL_FILE = config["val_path"]

    train_dataset = WeatherDataset(TRAIN_FILE, seq_len=60, forecast_horizon=7, target_cols=None)
    val_dataset = WeatherDataset(VAL_FILE, seq_len=60, forecast_horizon=7, target_cols=None)

    train_loader = DataLoader(
        train_dataset,
        batch_size=64,
        shuffle=True,
        num_workers=2,
        pin_memory=True,
        persistent_workers=True
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=64,
        shuffle=False,
        num_workers=2,
        pin_memory=True,
        persistent_workers=True
    )

    model = Transformer(
        num_features=len(train_dataset.feature_cols),
        num_stations=stats["num_stations"],
        d_model=128,
        nhead=8,
        num_layers=3,
        forecast_horizon=7,
        target_dim=len(train_dataset.target_cols)
    ).to(device)

    run_number = 2
    run_dir = Path(f"transformer/encoder_decoder/models/run{run_number}")
    model_path = run_dir / "transformer_model_finetuned2.pt"

    if not model_path.exists():
        print(f"No checkpoint found at {model_path}. Run phase 1 first.")
        return

    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    prior_train_losses = checkpoint.get("train_losses", [])
    prior_val_losses = checkpoint.get("val_losses", [])
    print(f"Loaded phase 1 weights from {model_path}")
    print(f"Phase 1 final val loss: {prior_val_losses[-1]:.4f}\n")

    criterion = nn.HuberLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-5)

    EPOCHS = 2
    train_losses = []
    val_losses = []

    for epoch in range(EPOCHS):
        start_time = time.time()

        tf_ratio = max(0.0, 1.0 - (epoch / (EPOCHS - 1))) if EPOCHS > 1 else 0.0

        model.train()
        total_loss = 0
        for X, Y, station_id in train_loader:
            X, Y, station_id = X.to(device), Y.to(device), station_id.to(device)
            optimizer.zero_grad()
            pred = scheduled_sampling_forward(model, X, Y, station_id, tf_ratio, device)
            loss = criterion(pred, Y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += loss.item()

        train_loss_epoch = total_loss / len(train_loader)
        train_losses.append(train_loss_epoch)

        model.eval()
        val_loss = 0
        with torch.no_grad():
            for X, Y, station_id in val_loader:
                X, Y, station_id = X.to(device), Y.to(device), station_id.to(device)
                pred = scheduled_sampling_forward(model, X, Y, station_id, tf_ratio=0.0, device=device)
                loss = criterion(pred, Y)
                val_loss += loss.item()

        val_loss_epoch = val_loss / len(val_loader)
        val_losses.append(val_loss_epoch)

        epoch_time_min = (time.time() - start_time) / 60
        print(f"Epoch {epoch+1} | TF ratio: {tf_ratio:.2f} | Time: {epoch_time_min:.2f} mins")
        print(f"Train Loss: {train_loss_epoch:.4f}")
        print(f"Val Loss:   {val_loss_epoch:.4f}\n")

    save_path = run_dir / "transformer_model_finetuned3.pt"

    torch.save({
        "model_state_dict": model.state_dict(),
        "epochs": checkpoint.get("epochs", 0) + EPOCHS,
        "train_losses": prior_train_losses + train_losses,
        "val_losses": prior_val_losses + val_losses,
        "phase": "scheduled_sampling_finetune"
    }, save_path)

    print(f"Fine-tuned model saved at: {save_path}")


if __name__ == "__main__":
    main()