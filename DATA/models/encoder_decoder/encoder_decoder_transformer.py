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
        return x + self.pe[:, : x.size(1)].to(x.device)
    

class Transformer(nn.Module):
    def __init__(self, num_features, num_stations, d_model=128, nhead=8, num_layers=3, forecast_horizon=7, target_dim=3):
        super().__init__()
        self.input_proj = nn.Linear(num_features, d_model)
        self.target_proj = nn.Linear(target_dim, d_model)
        self.station_emb = nn.Embedding(num_stations, d_model)
        self.pos_enc = PositionalEncoding(d_model)

        self.transformer = nn.Transformer(
            d_model=d_model,
            nhead=nhead,
            num_encoder_layers=num_layers,
            num_decoder_layers=num_layers,
            dim_feedforward=256,
            dropout=0.1,
            batch_first=True
        )

        self.head = nn.Linear(d_model, target_dim)
        self.forecast_horizon = forecast_horizon
        self.target_dim = target_dim

    def generate_square_subsequent_mask(self, sz, device):
        mask = torch.triu(torch.ones(sz, sz, device=device) * float('-inf'), diagonal=1)
        return mask

    def forward(self, src, station_id, tgt):
        src = self.input_proj(src)
        station_emb = self.station_emb(station_id).unsqueeze(1)
        src = src + station_emb
        src = self.pos_enc(src)

        tgt = self.target_proj(tgt)
        tgt = tgt + station_emb
        tgt = self.pos_enc(tgt)
        tgt_mask = self.generate_square_subsequent_mask(tgt.size(1), src.device)

        output = self.transformer(src, tgt, tgt_mask=tgt_mask)
        out = self.head(output)
        return out
