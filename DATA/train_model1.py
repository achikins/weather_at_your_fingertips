import pandas as pd
import numpy as np
import joblib
import json
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping


print("Num GPUs Available:", len(tf.config.list_physical_devices('GPU')))
with open("config.json") as f:
    config = json.load(f)

INPUT_FILE = config["lstm_dataset_path"]

LOOKBACK = 30
HORIZON = 7

WEATHER_COLS = [
    "evapotranspiration(mm)",
    "rain(mm)",
    "maximum_temperature(°C)",
    "minimum_temperature(°C)",
    "maximum_relative_humidity(%)",
    "minimum_relative_humidity(%)",
    "average_10m_wind_speed(m/sec)"
]

df = pd.read_csv(INPUT_FILE)
df["date"] = pd.to_datetime(df["date"])

scaler = StandardScaler()
df[WEATHER_COLS] = scaler.fit_transform(df[WEATHER_COLS])
joblib.dump(scaler, "lstm_scaler.pkl")

mask_col = [col + "_mask" for col in WEATHER_COLS]
FEATURES = WEATHER_COLS + mask_col + [
    "station_id",
    "sin_day",
    "cos_day"
]

x = []
y = []
for station_id, group in df.groupby("station_id"):
    group = group.sort_values("date")
    data = group[FEATURES].values
    targets = group[WEATHER_COLS].values
    for i in range(len(group) - LOOKBACK - HORIZON + 1):
        x.append(data[i : i+LOOKBACK])
        y.append(targets[i+LOOKBACK : i+LOOKBACK+HORIZON ])

x = np.array(x, dtype=np.float32)
y = np.array(y, dtype=np.float32)
print("X shape:", x.shape)
print("Y shape:", y.shape)

split_index = int(len(x) * 0.8)
x_train = x[:split_index]
y_train = y[:split_index]
x_val = x[split_index:]
y_val = y[split_index:]
print("Training samples:", len(x_train))
print("Validation samples", len(x_val))

model = Sequential([
    LSTM(
        64,
        return_sequences = True,
        input_shape = (LOOKBACK, len(FEATURES))
    ),
    Dropout(0.2),
    LSTM(32),
    Dense(HORIZON * len(WEATHER_COLS))
])

model.compile(
    optimizer = "adam",
    loss = "mse"
)

model.summary()

y_train = y_train.reshape(y_train.shape[0], -1)
y_val = y_val.reshape(y_val.shape[0], -1)

print("Training model ...")

history = model.fit(
    x_train,
    y_train,
    validation_data = (x_val, y_val),
    epochs = 50,
    batch_size = 256,
    callbacks = [EarlyStopping(
        monitor="val_loss",
        patience=5,
        restore_best_weights=True
    )]
)

print("Save model ...")
model.save("lstm_model.h5")