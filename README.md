# PSS – Railway/Docker Template

## Local Dev
1) Copy `.env.example` → `.env` and set `KORASTATS_API_KEY`.
2) `docker compose up --build`
3) Visit:
   - DB: localhost:5432 (pss/pss)
   - Backend: http://localhost:8000/docs
   - n8n: http://localhost:5678
   - Interface: http://localhost:8501

## Running ETL
- Open Interface → “Run ETL”, or:
  ```bash
  curl -X POST "http://localhost:8000/run/etl?limit_seasons=1&limit_matches=5"