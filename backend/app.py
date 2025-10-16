from fastapi import FastAPI
from etl import run_etl
from compute_metrics import compute_player_match_minutes
import os

# Try loading .env if running locally
if os.getenv("RAILWAY_ENVIRONMENT") is None:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded local .env file")

# Now safely access your environment variables
api_key = os.getenv("KORASTATS_API_KEY")

if not api_key:
    print("❌ Set KORASTATS_API_KEY env var.")
    exit(1)
else:
    print("✅ KORASTATS_API_KEY loaded successfully.")
app = FastAPI(title="PSS Backend")

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/run/etl")
def run_etl_endpoint(limit_seasons: int | None = None, limit_matches: int | None = None):
    run_etl(limit_seasons, limit_matches)
    return {"status": "done"}

@app.post("/run/compute")
def run_compute_endpoint():
    compute_player_match_minutes()
    return {"status": "metrics computed"}
