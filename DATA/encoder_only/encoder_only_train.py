import time
import sys
import math
import torch
import torch.nn as nn
import torch.optim as optim
import json
import psycopg2
from pathlib import Path
from torch.utils.data import DataLoader

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.dataset import WeatherDataset
from encoder_only_transformer import Transformer
from utils.get_device import get_device
from utils.load_from_db import load_stats


TARGET_COLS = [
    "rain_mm",
    "max_temp_c",
    "min_temp_c",
    "max_humidity_pct",
    "min_humidity_pct",
    "avg_wind_speed_mps"
]


# -----------------------------
# Loss
# -----------------------------
def weighted_huber_loss(pred, target, feat_weights, horiz_weights, delta=1.0):
    loss_fn = nn.HuberLoss(reduction="none", delta=delta)
    loss = loss_fn(pred, target)

    loss = loss * feat_weights.view(1, 1, -1)
    loss = loss * horiz_weights.view(1, -1, 1)

    return loss.mean()


# -----------------------------
# Scheduler
# -----------------------------
def get_lr_lambda(warmup_epochs, total_epochs, min_lr_ratio=0.01):
    def lr_lambda(epoch):
        if epoch < warmup_epochs:
            return (epoch + 1) / warmup_epochs
        progress = (epoch - warmup_epochs) / max(1, total_epochs - warmup_epochs)
        cosine = 0.5 * (1 + math.cos(math.pi * progress))
        return min_lr_ratio + (1 - min_lr_ratio) * cosine
    return lr_lambda


# -----------------------------
# Early stopping
# -----------------------------
class EarlyStopping:
    def __init__(self, patience=10, min_delta=1e-4, verbose=True):
        self.patience = patience
        self.min_delta = min_delta
        self.verbose = verbose
        self.counter = 0
        self.best_loss = None
        self.early_stop = False

    def step(self, val_loss):
        if self.best_loss is None or val_loss < self.best_loss - self.min_delta:
            self.best_loss = val_loss
            self.counter = 0
            return True
        else:
            self.counter += 1
            if self.verbose:
                print(f"  EarlyStopping: {self.counter}/{self.patience}")
            if self.counter >= self.patience:
                self.early_stop = True
            return False

    def state_dict(self):
        return {
            "counter": self.counter,
            "best_loss": self.best_loss,
            "early_stop": self.early_stop
        }

    def load_state_dict(self, state):
        self.counter = state["counter"]
        self.best_loss = state["best_loss"]
        self.early_stop = state["early_stop"]


# -----------------------------
# Main
# -----------------------------
def main():

    run_number          = 13
    EPOCHS_THIS_SESSION = 15
    TOTAL_EPOCHS        = 50
    WARMUP_EPOCHS       = 3

    db_url = "postgresql://postgres:password@localhost:5432/weather_at_your_fingertips_db"
    conn = psycopg2.connect(db_url)
    config_path = Path(__file__).parent.parent / "utils/config.json"
    device      = get_device()

    with open(config_path) as f:
        config = json.load(f)
    stats = load_stats(conn, 1)

    # -----------------------------
    # Dataset
    # -----------------------------
    train_dataset = WeatherDataset(
        config["train_path"],
        seq_len=60,
        forecast_horizon=7,
        target_cols=None
    )

    val_dataset = WeatherDataset(
        config["val_path"],
        seq_len=60,
        forecast_horizon=7,
        target_cols=None
    )

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

    # -----------------------------
    # Model
    # -----------------------------
    model = Transformer(
        num_features=len(train_dataset.feature_cols),
        num_stations=stats["num_stations"],
        d_model=64,
        nhead=4,
        num_layers=3,
        forecast_horizon=7,
        target_dim=len(train_dataset.target_cols),
        dropout=0.15
    ).to(device)

    # -----------------------------
    # Loss weights
    # -----------------------------
    stds = torch.tensor([stats[col]["std"] for col in TARGET_COLS], device=device)
    feat_weights = 1.0 / (stds + 1e-8)
    feat_weights = feat_weights / feat_weights.mean()

    horiz_weights = torch.tensor(
        [2.0, 1.5, 1.2, 1.0, 1.0, 1.0, 1.0],
        device=device
    )
    horiz_weights = horiz_weights / horiz_weights.mean()

    # -----------------------------
    # Optim + Scheduler
    # -----------------------------
    optimizer = optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-3)

    scheduler = torch.optim.lr_scheduler.LambdaLR(
        optimizer,
        lr_lambda=get_lr_lambda(WARMUP_EPOCHS, TOTAL_EPOCHS, 0.01)
    )

    early_stopper = EarlyStopping(patience=15, min_delta=1e-4)

    # -----------------------------
    # Checkpoint
    # -----------------------------
    run_dir = Path(f"models/encoder_only/models/run{run_number}")
    run_dir.mkdir(parents=True, exist_ok=True)

    best_path = run_dir / "best_model.pt"
    last_path = run_dir / "last_model.pt"

    start_epoch = 0
    best_val_loss = float("inf")

    train_losses, val_losses = [], []

    # -----------------------------
    # Resume
    # -----------------------------
    if last_path.exists():
        print(f"Resuming from {last_path}")
        checkpoint = torch.load(last_path, map_location=device)

        model.load_state_dict(checkpoint["model_state_dict"])
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        early_stopper.load_state_dict(checkpoint["early_stopper_state"])

        start_epoch = checkpoint["epoch"]
        train_losses = checkpoint["train_losses"]
        val_losses = checkpoint["val_losses"]
        best_val_loss = checkpoint["best_val_loss"]

    # -----------------------------
    # Training loop
    # -----------------------------
    end_epoch = start_epoch + EPOCHS_THIS_SESSION

    print(f"\nTraining epochs {start_epoch+1} → {end_epoch}\n")

    for epoch in range(start_epoch, end_epoch):

        start_time = time.time()

        # ================= TRAIN =================
        model.train()
        train_loss = 0

        for X, Y, station_id in train_loader:
            X, Y, station_id = X.to(device), Y.to(device), station_id.to(device)

            optimizer.zero_grad()

            pred = model(X, station_id)

            loss = weighted_huber_loss(
                pred, Y,
                feat_weights,
                horiz_weights,
                delta=1.0
            )

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            train_loss += loss.item() * X.size(0)

        train_loss /= len(train_dataset)
        train_losses.append(train_loss)

        # ================= VALIDATION =================
        model.eval()
        val_loss = 0

        with torch.no_grad():
            for X, Y, station_id in val_loader:
                X, Y, station_id = X.to(device), Y.to(device), station_id.to(device)

                pred = model(X, station_id)

                loss = weighted_huber_loss(
                    pred, Y,
                    feat_weights,
                    horiz_weights,
                    delta=1.0
                )

                val_loss += loss.item() * X.size(0)

        val_loss /= len(val_dataset)
        val_losses.append(val_loss)

        # ================= STEP SCHEDULER =================
        scheduler.step()
        lr = scheduler.get_last_lr()[0]

        # ================= EARLY STOP =================
        improved = early_stopper.step(val_loss)
        if improved:
            best_val_loss = val_loss

        # ================= SAVE CHECKPOINTS =================
        torch.save({
            "epoch": epoch + 1,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict(),
            "early_stopper_state": early_stopper.state_dict(),
            "train_losses": train_losses,
            "val_losses": val_losses,
            "best_val_loss": best_val_loss
        }, last_path)

        if improved:
            torch.save(model.state_dict(), best_path)
            print(f"  ✅ New best model saved ({best_val_loss:.4f})")

        # ================= LOG =================
        epoch_time = (time.time() - start_time) / 60

        print(
            f"Epoch {epoch+1}/{TOTAL_EPOCHS} | "
            f"LR: {lr:.2e} | "
            f"Time: {epoch_time:.2f} min"
        )
        print(f"  Train: {train_loss:.4f} | Val: {val_loss:.4f}")

        if early_stopper.early_stop:
            print("\nEarly stopping triggered.")
            break

    print("\nTraining complete.")
    print(f"Best Val Loss: {best_val_loss:.4f}")
    print(f"Best model saved at: {best_path}")


if __name__ == "__main__":
    main()