import time
import torch
import torch.nn as nn
import torch.optim as optim
import json
from pathlib import Path
from datetime import datetime
from torch.utils.data import DataLoader
from dataset import WeatherDataset
from transformer import Transformer
from get_device import get_device


class EarlyStopping:
    """Stops training if validation loss doesn't improve after patience epochs."""
    def __init__(self, patience=5, min_delta=1e-4, verbose=True):
        self.patience = patience
        self.min_delta = min_delta
        self.verbose = verbose
        self.counter = 0
        self.best_loss = None
        self.early_stop = False

    def step(self, val_loss):
        if self.best_loss is None:
            self.best_loss = val_loss
        elif val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.verbose:
                print(f"EarlyStopping counter: {self.counter} / {self.patience}")
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_loss = val_loss
            self.counter = 0


def main():
    # Load config
    config_path = Path(__file__).parent.parent / "config.json"
    device = get_device()

    with open(config_path) as f:
        config = json.load(f)

    TRAIN_FILE = config["train_path"]
    VAL_FILE = config["val_path"]
    TEST_FILE = config["test_path"]

    # Datasets
    train_dataset = WeatherDataset(TRAIN_FILE, seq_len=60, forecast_horizon=7, target_cols=None)
    val_dataset = WeatherDataset(VAL_FILE, seq_len=60, forecast_horizon=7, target_cols=None)
    test_dataset = WeatherDataset(TEST_FILE, seq_len=60, forecast_horizon=7, target_cols=None)

    # DataLoaders
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True, num_workers=2, pin_memory=True, persistent_workers=True)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False, num_workers=2, pin_memory=True, persistent_workers=True)
    test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False, num_workers=2, pin_memory=True, persistent_workers=True)

    # Model
    model = Transformer(
        num_features=len(train_dataset.feature_cols),
        num_stations=505,
        d_model=128,
        nhead=8,
        num_layers=3,
        forecast_horizon=7,
        target_dim=len(train_dataset.target_cols)
    ).to(device)

    # Load latest checkpoint if exists
    checkpoints_dir = Path("transformer")
    checkpoints_dir.mkdir(exist_ok=True)
    existing_checkpoints = sorted(checkpoints_dir.glob("transformer_model_weights_*.pt"))
    if existing_checkpoints:
        latest_ckpt = existing_checkpoints[-1]
        print(f"Loading existing weights from {latest_ckpt.name}")
        model.load_state_dict(torch.load(latest_ckpt, map_location=device))

    # Loss and optimizer
    criterion = nn.HuberLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-4)

    # Training settings
    EPOCHS = 50
    early_stopper = EarlyStopping(patience=5, min_delta=1e-4, verbose=True)
    best_val_loss = float("inf")

    # Timestamp for new checkpoint
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    checkpoint_path = checkpoints_dir / f"transformer_model_weights_{timestamp}.pt"

    for epoch in range(EPOCHS):
        start_time = time.time()

        # Train
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

        # Validation
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for X, Y, station_id in val_loader:
                X, Y, station_id = X.to(device), Y.to(device), station_id.to(device)
                pred = model(X, station_id)
                loss = criterion(pred, Y)
                val_loss += loss.item()

        avg_train_loss = total_loss / len(train_loader)
        avg_val_loss = val_loss / len(val_loader)
        epoch_time_min = (time.time() - start_time) / 60

        print(f"Epoch {epoch+1} | Time: {epoch_time_min:.2f} mins")
        print(f"Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")

        # Save best model
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save(model.state_dict(), checkpoint_path)
            print(f"Saved new best model: {checkpoint_path.name}")

        # Early stopping
        early_stopper.step(avg_val_loss)
        if early_stopper.early_stop:
            print("Early stopping triggered.")
            break

    print("Training complete.")


if __name__ == "__main__":
    main()