"""Copy production (Supabase) into local Postgres (dev), only what local is missing or has stale.

Run from backend/:  uv run python -m app.pull_prod
Reads the Supabase URL from .env.production and only ever reads from it. RS ratings aren't copied:
they're rebuilt locally from daily_bars, exactly as the Daily refresh does. chat_usage stays local.
"""

import math
from urllib.parse import urlparse

import psycopg
from dotenv import dotenv_values

from app.config import BACKEND_DIR, DATABASE_URL
from app.db import CONNECT_KWARGS, Row, connect, init_schema, one
from app.etl import compute_rs

PRODUCTION_ENV = BACKEND_DIR / ".env.production"
# Small enough to replace whole on every run
SMALL_TABLES = [
    "companies",
    "fetched_dates",
    "splits_applied",
    "history_checked",
    "company_profiles",
    "market_directions",
    "blurbs",
]
LOCAL_HOSTS = {None, "", "localhost", "127.0.0.1", "::1"}  # None: a Unix socket

Fingerprints = dict[str, tuple[int, float]]


def is_local(url: str) -> bool:
    return urlparse(url).hostname in LOCAL_HOSTS


def production_url() -> str:
    url = dotenv_values(PRODUCTION_ENV).get("DATABASE_URL") if PRODUCTION_ENV.exists() else None
    if not url:
        raise SystemExit(f"No DATABASE_URL in {PRODUCTION_ENV}; add the Supabase session-pooler URL there")
    return url


def columns(conn: psycopg.Connection[Row], table: str) -> str:
    rows = conn.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position", (table,)
    ).fetchall()
    return ", ".join(r["column_name"] for r in rows)


def copy(src: psycopg.Connection[Row], dst: psycopg.Connection[Row], table: str, where: str = "", params=()) -> int:
    """Stream the matching rows of a table from src into dst; returns how many were copied."""
    cols = columns(dst, table)
    with src.cursor().copy(f"COPY (SELECT {cols} FROM {table} {where}) TO STDOUT", params) as out:
        with dst.cursor() as cur:
            with cur.copy(f"COPY {table} ({cols}) FROM STDIN") as into:
                for data in out:
                    into.write(data)
            return cur.rowcount


def fingerprints(conn: psycopg.Connection[Row], through: str) -> Fingerprints:
    """Each ticker's bar count and close sum up to a date, to spot history the ETL rewrote."""
    rows = conn.execute(
        "SELECT ticker, COUNT(*) AS n, SUM(close) AS total FROM daily_bars WHERE date <= %s GROUP BY ticker", (through,)
    ).fetchall()
    return {r["ticker"]: (r["n"], r["total"]) for r in rows}


def changed_tickers(local: Fingerprints, remote: Fingerprints) -> list[str]:
    """Tickers whose history differs, such as after a split adjustment or a rename rebuild."""
    changed = []
    for ticker in sorted(local.keys() | remote.keys()):
        a, b = local.get(ticker), remote.get(ticker)
        if a is None or b is None or a[0] != b[0] or not math.isclose(a[1], b[1], rel_tol=1e-9):
            changed.append(ticker)
    return changed


def main() -> None:
    if not is_local(DATABASE_URL):
        raise SystemExit("DATABASE_URL isn't local Postgres; pull_prod only writes to a local database")
    local = connect()
    remote = psycopg.Connection[Row].connect(production_url(), **CONNECT_KWARGS)
    remote.execute("SET default_transaction_read_only = on")
    init_schema(local)

    local_max = one(local.execute("SELECT MAX(date) FROM daily_bars"))[0]
    with local.transaction():
        for table in SMALL_TABLES:
            local.execute(f"DELETE FROM {table}")
            print(f"{table}: {copy(remote, local, table)} rows")
        if local_max is None:
            print(f"daily_bars: {copy(remote, local, 'daily_bars')} rows (full copy)")
        else:
            changed = changed_tickers(fingerprints(local, local_max), fingerprints(remote, local_max))
            if changed:
                local.execute("DELETE FROM daily_bars WHERE ticker = ANY(%s)", (changed,))
                recopied = copy(remote, local, "daily_bars", "WHERE ticker = ANY(%s)", (changed,))
                print(f"daily_bars: {len(changed)} tickers re-copied ({recopied} rows): {', '.join(changed[:10])}"
                      + (" …" if len(changed) > 10 else ""))  # fmt: skip
            new = copy(remote, local, "daily_bars", "WHERE date > %s AND NOT (ticker = ANY(%s))", (local_max, changed))
            print(f"daily_bars: +{new} rows after {local_max}")
    compute_rs(local)
    rated = one(local.execute("SELECT MAX(date) FROM rs_ratings"))[0]
    print(f"\nLocal is up to date with production through {rated}")


if __name__ == "__main__":
    main()
