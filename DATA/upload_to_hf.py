from huggingface_hub import HfApi, upload_file
import json, shutil
from pathlib import Path

REPO_ID = "theyeehong/weather_forecast_api"

api = HfApi()
api.create_repo(REPO_ID, exist_ok=True)

api.upload_file(
    path_or_fileobj="models/encoder_only/models/run12/last_model.pt",
    path_in_repo="last_model.pt",
    repo_id=REPO_ID,
)

api.upload_file(
    path_or_fileobj="transformer_stats.json",
    path_in_repo="transformer_stats.json",
    repo_id=REPO_ID,
)

print(f"Uploaded to https://huggingface.co/{REPO_ID}")


files = api.list_repo_files(repo_id=REPO_ID)

for f in files:
    print(f)
