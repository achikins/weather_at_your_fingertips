import torch
import torch.nn as nn
import math


class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=500):
        super().__init__()

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1)

        div_term = torch.exp(
            torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model)
        )

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)

        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x):
        return x + self.pe[:, :x.size(1)]


class Transformer(nn.Module):
    def __init__(self,num_features,num_stations,d_model=128,nhead=8,num_layers=3,forecast_horizon=7,target_dim=6,dropout=0.1):
        super().__init__()

        self.pos_enc = PositionalEncoding(d_model)
        self.forecast_horizon = forecast_horizon
        self.target_dim = target_dim
        self.input_proj = nn.Linear(num_features, d_model)
        self.input_dropout = nn.Dropout(dropout)
        self.station_emb = nn.Embedding(num_stations, d_model)
        self.cls_token = nn.Parameter(torch.zeros(1, 1, d_model))
        nn.init.trunc_normal_(self.cls_token, std=0.02)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 2,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True
        )

        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers
        )

        self.head = nn.Sequential(
            nn.LayerNorm(d_model),
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, forecast_horizon * target_dim)
        )

    def forward(self, x, station_id):
        B, T, _ = x.shape
        x = self.input_proj(x)
        x = self.input_dropout(x)
        station_emb = self.station_emb(station_id).unsqueeze(1)
        x = x + station_emb
        cls = self.cls_token.expand(B, -1, -1)
        x = torch.cat([cls, x], dim=1)
        x = self.pos_enc(x)
        x = self.transformer(x)
        cls_out = x[:, 0, :]
        out = self.head(cls_out)

        return out.view(B, self.forecast_horizon, self.target_dim)