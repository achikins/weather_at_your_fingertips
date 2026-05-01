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
        self.pe = pe.unsqueeze(0)

    def forward(self, x):
        return x + self.pe[:, :x.size(1)].to(x.device)


class Transformer(nn.Module):
    def __init__(self,num_features,num_stations,d_model=256,nhead=8,num_layers=4,forecast_horizon=7,target_dim=6,dropout=0.1):
        super().__init__()
        self.input_proj = nn.Linear(num_features, d_model)
        self.station_emb = nn.Embedding(num_stations, d_model)
        self.pos_enc = PositionalEncoding(d_model)

        self.cls_token = nn.Parameter(torch.zeros(1, 1, d_model))
        nn.init.trunc_normal_(self.cls_token, std=0.02)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.head = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, forecast_horizon * target_dim)
        )

        self.forecast_horizon = forecast_horizon
        self.target_dim = target_dim

    def forward(self, x, station_id):
        x = self.input_proj(x)
        station_emb = self.station_emb(station_id).unsqueeze(1)
        x = x + station_emb
        x = self.pos_enc(x)
        cls = self.cls_token.expand(x.size(0), -1, -1)
        x = torch.cat([cls, x], dim=1)
        x = self.transformer(x)
        cls_out = x[:, 0, :]
        out = self.head(cls_out)
        return out.view(-1, self.forecast_horizon, self.target_dim)