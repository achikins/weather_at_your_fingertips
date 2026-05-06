import argparse
import os
import psycopg2
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from psycopg2.extras import execute_values
from torch.utils.data import DataLoader
from utils.get_device import get_device
from utils.latest_window_dataset import LatestWindowDataset, denormalise
from utils.predict import load_encoder_only, load_encoder_decoder, predict_encoder_only, predict_encoder_decoder
from utils.load_from_db import load_station_mapping, load_stats, load_latest_window_data
from utils.download_data import run_download_data
from utils.combine_data import run_combine_data
from utils.clean_data_wo_imputation import run_clean_data_wo_imputation
from utils.load_to_db import run_load_to_db


load_dotenv()


def run_data_pipeline():
    run_download_data()
    run_combine_data()
    run_clean_data_wo_imputation()
    run_load_to_db()


def get_db_connection():
    db_url = "postgresql://postgres:password@localhost:5432/weather_at_your_fingertips_db"
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    conn = psycopg2.connect(db_url)
    return conn


def reset_predictions_table(conn):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM forecasts")
    conn.commit()


def build_forecast_rows(preds, metadata, station_map, stats):
    rows = []
    generated_at = datetime.now()
    for i, (station_id, last_date) in enumerate(metadata):
        pred_denorm = denormalise(preds[i], stats)
        for day in range(7):
            forecast_date = last_date + pd.Timedelta(days=day + 1)
            rows.append((
                station_id,
                forecast_date.date(),
                generated_at,
                day + 1,
                round(float(pred_denorm[day][1]), 4),   # max_temp     index 1
                round(float(pred_denorm[day][2]), 4),   # min_temp     index 2
                round(float(pred_denorm[day][0]), 4),   # rain         index 0
                round(float(pred_denorm[day][3]), 4),   # max_humidity index 3
                round(float(pred_denorm[day][4]), 4),   # min_humidity index 4
                round(float(pred_denorm[day][5]), 4)    # wind_speed   index 5
            ))
    return rows


def insert_forecasts(conn, rows):
    query = """
        INSERT INTO forecasts (
            station_id, 
            forecast_date, 
            generated_at, 
            horizon_days,
            pred_max_temp_c,
            pred_min_temp_c,
            pred_rain_mm,
            pred_max_humidity_pct,
            pred_min_humidity_pct,
            pred_wind_speed_ms)
        VALUES %s
    """
    with conn.cursor() as cur:
        execute_values(cur, query, rows)
    conn.commit()



def main():
    device = get_device()

    # run_data_pipeline()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        choices=["encoder_only", "encoder_decoder"],
        default="encoder_only"
    )
    parser.add_argument(
        "--run",
        default="12"
    )
    parser.add_argument(
        "--type",
        choices=["best", "last"],
        default="best"
    )
    parser.add_argument(
        "--stats_id",
        default="1"
    )    
    args = parser.parse_args()

    conn = get_db_connection()
    station_map = load_station_mapping(conn)
    stats = load_stats(conn, args.stats_id)
    df = load_latest_window_data(conn, stats)

    dataset = LatestWindowDataset(df, seq_len=60)
    loader = DataLoader(dataset, batch_size=64, shuffle=False, num_workers=2)
    metadata = dataset.get_metadata()
    num_features = len(dataset.feature_cols)
    print(f"Found {len(dataset)} stations with sufficient history\n")

    if args.model == "encoder_only":
        model_path = Path(f"encoder_only/models/run{args.run}/{args.type}_model.pt")
        model = load_encoder_only(stats, num_features, device, model_path)
        preds = predict_encoder_only(model, loader, device)
    else:
        model_path = Path(f"encoder_decoder/models/run{args.run}/{args.type}_model.pt")
        model = load_encoder_decoder(stats, num_features, device, model_path)
        preds = predict_encoder_decoder(model, loader, device)
    
    reset_predictions_table(conn)
    rows = build_forecast_rows(preds, metadata, station_map, stats)
    insert_forecasts(conn, rows)
    print(f"Inserted {len(rows)} forecast rows into the database")


if __name__ == "__main__":
    main()