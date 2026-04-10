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

    criterion = nn.HuberLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-4)

    EPOCHS = 10
    train_losses = []
    val_losses = []

    for epoch in range(EPOCHS):
        start_time = time.time()

        # ===== TRAIN =====
        model.train()
        total_loss = 0
        for X, Y, station_id in train_loader:
            X, Y, station_id = X.to(device), Y.to(device), station_id.to(device)
            optimizer.zero_grad()

            Y_input = torch.zeros_like(Y)
            Y_input[:, 1:, :] = Y[:, :-1, :]
            Y_input[:, 0, :] = 0

            pred = model(X, station_id, Y_input)
            loss = criterion(pred, Y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += loss.item()

        train_loss_epoch = total_loss / len(train_loader)
        train_losses.append(train_loss_epoch)

        # ===== VALIDATION =====
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for X, Y, station_id in val_loader:
                X, Y, station_id = X.to(device), Y.to(device), station_id.to(device)

                Y_input = torch.zeros_like(Y)
                Y_input[:, 1:, :] = Y[:, :-1, :]
                Y_input[:, 0, :] = 0

                pred = model(X, station_id, Y_input)
                loss = criterion(pred, Y)
                val_loss += loss.item()

        val_loss_epoch = val_loss / len(val_loader)
        val_losses.append(val_loss_epoch)

        epoch_time_min = (time.time() - start_time) / 60
        print(f"Epoch {epoch+1} | Time: {epoch_time_min:.2f} mins")
        print(f"Train Loss: {train_loss_epoch:.4f}")
        print(f"Val Loss: {val_loss_epoch:.4f}\n")

    # ===== SAVE =====
    run_number = 2
    run_dir = Path(f"transformer/encoder_decoder/models/run{run_number}")
    run_dir.mkdir(parents=True, exist_ok=True)
    save_path = run_dir / "transformer_model.pt"

    torch.save({
        "model_state_dict": model.state_dict(),
        "epochs": EPOCHS,
        "train_losses": train_losses,
        "val_losses": val_losses,
        "phase": "teacher_forcing"
    }, save_path)

    print(f"Model saved at: {save_path}")


if __name__ == "__main__":
    main()