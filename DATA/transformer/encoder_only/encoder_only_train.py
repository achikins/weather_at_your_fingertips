import time
import sys
import math
import torch
import torch.nn as nn
import torch.optim as optim
import json
from pathlib import Path
from torch.utils.data import DataLoader
sys.path.append(str(Path(__file__).parent.parent))
from dataset import WeatherDataset
from encoder_only.encoder_only_transformer import Transformer
from get_device import get_device


TARGET_COLS = [
    "rain(mm)",
    "maximum_temperature(°C)",
    "minimum_temperature(°C)",
    "maximum_relative_humidity(%)",
    "minimum_relative_humidity(%)",
    "average_10m_wind_speed(m/sec)"
]


def weighted_huber_loss(pred, target, feat_weights, horiz_weights):
    loss = nn.HuberLoss(reduction="none")(pred, target)
    loss = loss * feat_weights.view(1, 1, -1)
    loss = loss * horiz_weights.view(1, -1, 1)
    return loss.mean()


def get_lr_lambda(warmup_epochs, total_epochs, min_lr_ratio=0.01):
    def lr_lambda(epoch):
        if epoch < warmup_epochs:
            return (epoch + 1) / warmup_epochs
        progress = (epoch - warmup_epochs) / max(1, total_epochs - warmup_epochs)
        cosine = 0.5 * (1 + math.cos(math.pi * progress))
        return min_lr_ratio + (1 - min_lr_ratio) * cosine
    return lr_lambda


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


def main():
    # ------------------------------------------------------------------ #
    #  CONFIG — edit these before each session                            #
    # ------------------------------------------------------------------ #
    run_number          = 4
    EPOCHS_THIS_SESSION = 3
    TOTAL_EPOCHS        = 50
    WARMUP_EPOCHS       = 3
    # ------------------------------------------------------------------ #

    config_path = Path(__file__).parent.parent.parent / "config.json"
    stats_path  = Path(__file__).parent.parent / "transformer_stats.json"
    device      = get_device()

    with open(config_path) as f:
        config = json.load(f)
    with open(stats_path) as f:
        stats = json.load(f)

    TRAIN_FILE = config["train_path"]
    VAL_FILE   = config["val_path"]

    train_dataset = WeatherDataset(TRAIN_FILE, seq_len=90, forecast_horizon=7, target_cols=None)
    val_dataset   = WeatherDataset(VAL_FILE,   seq_len=90, forecast_horizon=7, target_cols=None)

    train_loader = DataLoader(
        train_dataset, batch_size=64, shuffle=True,
        num_workers=2, pin_memory=True, persistent_workers=True
    )
    val_loader = DataLoader(
        val_dataset, batch_size=64, shuffle=False,
        num_workers=2, pin_memory=True, persistent_workers=True
    )

    model = Transformer(
        num_features=len(train_dataset.feature_cols),
        num_stations=stats["num_stations"],
        d_model=256,
        nhead=8,
        num_layers=4,
        forecast_horizon=7,
        target_dim=len(train_dataset.target_cols)
    ).to(device)

    stds = torch.tensor([stats[col]["std"] for col in TARGET_COLS], device=device)
    feat_weights  = 1.0 / (stds + 1e-8)
    feat_weights  = feat_weights / feat_weights.mean()
    horiz_weights = torch.tensor([2.0, 1.5, 1.2, 1.0, 1.0, 1.0, 1.0], device=device)
    horiz_weights = horiz_weights / horiz_weights.mean()

    optimizer = optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.LambdaLR(
        optimizer,
        lr_lambda=get_lr_lambda(WARMUP_EPOCHS, TOTAL_EPOCHS, min_lr_ratio=0.01)
    )
    early_stopper = EarlyStopping(patience=10, min_delta=1e-4, verbose=True)

    run_dir   = Path(f"transformer/encoder_only/models/run{run_number}")
    run_dir.mkdir(parents=True, exist_ok=True)
    save_path = run_dir / "transformer_model.pt"
    start_epoch   = 0
    train_losses  = []
    val_losses    = []
    best_val_loss = float("inf")

    if save_path.exists():
        print(f"Resuming from checkpoint: {save_path}")
        checkpoint = torch.load(save_path, map_location=device)
        model.load_state_dict(checkpoint["model_state_dict"])
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        early_stopper.load_state_dict(checkpoint["early_stopper_state"])
        start_epoch   = checkpoint["epoch"]
        train_losses  = checkpoint["train_losses"]
        val_losses    = checkpoint["val_losses"]
        best_val_loss = checkpoint["best_val_loss"]
        print(f"Resumed at epoch {start_epoch} | Best val loss so far: {best_val_loss:.4f}\n")
    else:
        print(f"No checkpoint found — starting fresh\n")

    if early_stopper.early_stop:
        print("Early stopping was already triggered in a previous session. Training complete.")
        return

    end_epoch = start_epoch + EPOCHS_THIS_SESSION

    print(f"Training epochs {start_epoch + 1} → {end_epoch}  (total budget: {TOTAL_EPOCHS})")
    print(f"Features: {len(train_dataset.feature_cols)} | Stations: {stats['num_stations']}\n")

    for epoch in range(start_epoch, end_epoch):
        start_time = time.time()

        # ===== TRAIN =====
        model.train()
        total_loss = 0
        for X, Y, station_id in train_loader:
            X, Y, station_id = X.to(device), Y.to(device), station_id.to(device)
            optimizer.zero_grad()
            pred = model(X, station_id)
            loss = weighted_huber_loss(pred, Y, feat_weights, horiz_weights)
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
                pred = model(X, station_id)
                loss = weighted_huber_loss(pred, Y, feat_weights, horiz_weights)
                val_loss += loss.item()

        val_loss_epoch = val_loss / len(val_loader)
        val_losses.append(val_loss_epoch)

        current_lr     = scheduler.get_last_lr()[0]
        epoch_time_min = (time.time() - start_time) / 60

        print(f"Epoch {epoch + 1:03d}/{TOTAL_EPOCHS} | LR: {current_lr:.2e} | Time: {epoch_time_min:.2f} mins")
        print(f"  Train Loss: {train_loss_epoch:.4f} | Val Loss: {val_loss_epoch:.4f}")

        scheduler.step()

        # save every epoch so resume is always possible
        improved = early_stopper.step(val_loss_epoch)
        if improved:
            best_val_loss = val_loss_epoch

        torch.save({
            "epoch":                epoch + 1,
            "model_state_dict":     model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict(),
            "early_stopper_state":  early_stopper.state_dict(),
            "train_losses":         train_losses,
            "val_losses":           val_losses,
            "best_val_loss":        best_val_loss,
        }, save_path)

        if improved:
            print(f"  Saved best model (val loss: {best_val_loss:.4f})")

        if early_stopper.early_stop:
            print(f"\nEarly stopping triggered at epoch {epoch + 1}.")
            break

    print(f"\nSession complete. Trained epochs {start_epoch + 1} → {epoch + 1}.")
    print(f"Best val loss: {best_val_loss:.4f}")
    print(f"Checkpoint saved at: {save_path}")
    print(f"\nTo continue training, just run the script again.")


if __name__ == "__main__":
    main()