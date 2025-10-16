from fastapi import FastAPI
from etl import run_etl
from compute_metrics import compute_player_match_minutes

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