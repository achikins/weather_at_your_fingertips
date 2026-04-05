import time
import torch
import torch.nn as nn
import torch.optim as optim
import json
from pathlib import Path
from torch.utils.data import DataLoader
from dataset import WeatherDataset
from DATA.transformer.encoder_only.encoder_only_transformer import Transformer
from get_device import get_device


def main():
    config_path = Path(__file__).parent.parent / "config.json"
    device = get_device()

    with open(config_path) as f:
        config = json.load(f)

    TRAIN_FILE = config["train_path"]
    VAL_FILE = config["val_path"]
    TEST_FILE = config["test_path"]

    train_dataset = WeatherDataset(TRAIN_FILE, seq_len=60, forecast_horizon=7, target_cols=None)
    val_dataset = WeatherDataset(VAL_FILE, seq_len=60, forecast_horizon=7, target_cols=None)
    test_dataset = WeatherDataset(TEST_FILE, seq_len=60, forecast_horizon=7, target_cols=None)

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
    test_loader = DataLoader(
        test_dataset, 
        batch_size=64, 
        shuffle=False,
        num_workers=2,
        pin_memory=True,
        persistent_workers=True
    )

    model = Transformer(
        num_features=len(train_dataset.feature_cols),
        num_stations=505,
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

        model.train()
        total_loss = 0
        for X, Y, station_id in train_loader:
            X, Y, station_id = X.to(device), Y.to(device), station_id.to(device)
            optimizer.zero_grad()
            pred = model(X, station_id)
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
                pred = model(X, station_id)
                loss = criterion(pred, Y)
                val_loss += loss.item()
        val_loss_epoch = val_loss / len(val_loader)
        val_losses.append(val_loss_epoch)

        epoch_time_sec = time.time() - start_time
        epoch_time_min = epoch_time_sec / 60
        print(f"Epoch {epoch+1} | Time: {epoch_time_min:.2f} mins")
        print(f"Train Loss: {total_loss / len(train_loader):.4f}")
        print(f"Val Loss: {val_loss / len(val_loader):.4f}\n")

    base_dir = Path("transformer/encoder_only/models")
    base_dir.mkdir(parents=True, exist_ok=True)
    existing_runs = [
        d for d in base_dir.iterdir()
        if d.is_dir() and d.name.startswith("run")
    ]
    run_numbers = [
        int(d.name.replace("run", ""))
        for d in existing_runs
        if d.name.replace("run", "").isdigit()
    ]
    next_run = max(run_numbers, default=0) + 1
    run_dir = base_dir / f"run{next_run}"
    run_dir.mkdir()
    
    save_path = run_dir / "transformer_model.pt"
    torch.save({
        "model_state_dict": model.state_dict(),
        "config": config,
        "epochs": EPOCHS,
        "train_loss": train_losses,
        "val_loss": val_losses
    }, save_path)

    with open(run_dir / "config.json", "w") as f:
        json.dump(config, f, indent=4)

    print(f"Model saved at: {save_path}")

if __name__ == "__main__":
    main()
