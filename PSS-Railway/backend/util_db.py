import os
from contextlib import contextmanager
import psycopg

DSN = os.getenv("DATABASE_URL")

@contextmanager
def get_conn():
    with psycopg.connect(DSN, autocommit=False) as conn:
        yield conn

def upsert_many(conn, table: str, rows: list[dict], conflict_cols: list[str] | None = None):
    if not rows:
        return 0
    cols = sorted(rows[0].keys())
    placeholders = ", ".join([f"%({c})s" for c in cols])
    col_list = ", ".join(cols)
    if not conflict_cols:
        # assume single column PK named 'id' if present
        conflict_cols = ["id"] if "id" in cols else []
    conflict = f"ON CONFLICT ({', '.join(conflict_cols)}) DO UPDATE SET " + \
               ", ".join([f"{c}=EXCLUDED.{c}" for c in cols if c not in conflict_cols]) if conflict_cols else ""
    sql = f"INSERT INTO korastats.{table} ({col_list}) VALUES ({placeholders}) {conflict}"
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    return len(rows)