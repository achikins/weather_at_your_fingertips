import torch, json, os
import pandas as pd
import numpy as np
import psycopg2
from datetime import datetime, timezone
from pathlib import Path
from torch.utils.data import Dataset, DataLoader
from huggingface_hub import hf_hub_download
from data.encoder_only.encoder_only_transformer import Transformer as EncoderOnlyTransformer
from data.utils.latest_window_dataset import LatestWindowDataset, TARGET_COLS, denormalise
from backend.cron.cron_build_features import TARGET_COLS, NUMERIC_COLS, build_features, WindowDataset, denormalise


REPO_ID = "theyeehong/weather_forecast_api"

def get_conn():
    return psycopg2.connect(
        host="localhost",
        database="weather_at_your_fingertips_db",
        user="postgres",
        password="password",
        port=5432
    )


def main():
    device = torch.device("cpu")
    MODEL_PATH = hf_hub_download(repo_id=REPO_ID, filename="last_model.pt")
    STATS_PATH = hf_hub_download(repo_id=REPO_ID, filename="transformer_stats.json")

    with open(STATS_PATH, "r") as f:
        stats = json.load(f)

    conn = get_conn()
    df = pd.read_sql("""
        SELECT *
        FROM (
            SELECT 
                station_id,
                obs_date,
                evapotranspiration_mm,
                rain_mm,
                max_temp_c,
                min_temp_c,
                max_humidity_pct,
                min_humidity_pct,
                avg_wind_speed_mps,
                ROW_NUMBER() OVER (
                    PARTITION BY station_id
                    ORDER BY obs_date DESC
                ) AS rn
            FROM daily_weather
        ) t
        WHERE rn <= 100
        ORDER BY station_id, obs_date;
    """, conn)
    conn.close()

    df = build_features(df, stats)
    dataset = WindowDataset(df, seq_len=60)
    loader = DataLoader(dataset, batch_size=64, shuffle=False)

    if len(dataset) == 0:
        print("No stations with sufficient history")
        return
    
    model = EncoderOnlyTransformer(
        num_features=len(dataset.feature_cols),
        num_stations=stats["num_stations"],
        d_model=128,
        nhead=8,
        num_layers=3,
        forecast_horizon=7,
        target_dim=len(TARGET_COLS)
    ).to(device)

    checkpoint = torch.load(MODEL_PATH, map_location=device)
    if "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model.load_state_dict(checkpoint)

    model.eval()
    all_preds = []
    with torch.no_grad():
        for X, station_id in loader:
            X, station_id = X.to(device), station_id.to(device)
            pred = model(X, station_id)
            all_preds.append(pred.cpu().numpy())
    preds = np.concatenate(all_preds, axis=0)
    generated_at = datetime.now(timezone.utc)  

    rows = []
    for i, (station_id, last_date) in enumerate(dataset.metadata):
        pred_denorm = denormalise(preds[i], stats)
        for day in range(7):
            forecast_date = pd.Timestamp(last_date) + pd.Timedelta(days=day + 1)
            rows.append({
                "station_id":           station_id,
                "forecast_date":        forecast_date.date().isoformat(),
                "generated_at":         generated_at.isoformat(),
                "horizon_days":         day + 1,
                "pred_rain_mm":         round(float(pred_denorm[day, 0]), 2),
                "pred_max_temp_c":      round(float(pred_denorm[day, 1]), 2),
                "pred_min_temp_c":      round(float(pred_denorm[day, 2]), 2),
                "pred_max_humidity_pct": round(float(pred_denorm[day, 3]), 2),
                "pred_min_humidity_pct": round(float(pred_denorm[day, 4]), 2),
                "pred_wind_speed_ms":   round(float(pred_denorm[day, 5]), 2),
            })

    conn = get_conn()
    cur = conn.cursor()
    cur.executemany("""
        INSERT INTO forecasts (
            station_id,
            forecast_date,
            generated_at,
            horizon_days,
            pred_rain_mm,
            pred_max_temp_c,
            pred_min_temp_c,
            pred_max_humidity_pct,
            pred_min_humidity_pct,
            pred_wind_speed_ms
        ) VALUES (
            %(station_id)s,
            %(forecast_date)s,
            %(generated_at)s,
            %(horizon_days)s,
            %(pred_rain_mm)s,
            %(pred_max_temp_c)s,
            %(pred_min_temp_c)s,
            %(pred_max_humidity_pct)s,
            %(pred_min_humidity_pct)s,
            %(pred_wind_speed_ms)s
        )
        ON CONFLICT (station_id, forecast_date, horizon_days)
        DO UPDATE SET
            generated_at            = EXCLUDED.generated_at,
            pred_rain_mm            = EXCLUDED.pred_rain_mm,
            pred_max_temp_c         = EXCLUDED.pred_max_temp_c,
            pred_min_temp_c         = EXCLUDED.pred_min_temp_c,
            pred_max_humidity_pct   = EXCLUDED.pred_max_humidity_pct,
            pred_min_humidity_pct   = EXCLUDED.pred_min_humidity_pct,
            pred_wind_speed_ms      = EXCLUDED.pred_wind_speed_ms;
    """, rows)
    conn.commit()
    cur.close()
    conn.close()
    print(f"Done — {len(rows)} forecasts upserted for {len(dataset)} stations")

if __name__ == "__main__":
    main()

    