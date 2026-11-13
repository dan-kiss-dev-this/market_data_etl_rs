"""Copy production (Supabase) into local Postgres (dev), only what local is missing or has stale.

Run from backend/:  uv run python -m app.pull_prod
Reads the Supabase URL from .env.production and only ever reads from it. Every table is copied except
SKIPPED, using only the columns both databases have, so a schema change that one side doesn't have yet
is reported rather than fatal.
"""

import math

import psycopg
from dotenv import dotenv_values

from app.config import BACKEND_DIR, DATABASE_URL
from app.db import CONNECT_KWARGS, Row, connect, init_schema, is_local, one
from app.etl import compute_rs

PRODUCTION_ENV = BACKEND_DIR / ".env.production"
# Every other table is small enough to replace whole on every run
SKIPPED = {
    "daily_bars",  # copied incrementally below
    "rs_ratings",  # rebuilt locally from daily_bars, exactly as the Daily refresh does
    "chat_usage",  # stays local
    "schema_migrations",  # each database records its own
}

Fingerprints = dict[str, tuple[int, float]]
Schema = dict[str, list[str]]  # table -> its columns, in order


def production_url() -> str:
    url = dotenv_values(PRODUCTION_ENV).get("DATABASE_URL") if PRODUCTION_ENV.exists() else None
    if not url:
        raise SystemExit(f"No DATABASE_URL in {PRODUCTION_ENV}; add the Supabase session-pooler URL there")
    return url


def schema(conn: psycopg.Connection[Row]) -> Schema:
    rows = conn.execute(
        """SELECT c.table_name, c.column_name FROM information_schema.columns c
           JOIN information_schema.tables t USING (table_schema, table_name)
           WHERE c.table_schema = 'public' AND t.table_type = 'BASE TABLE'
           ORDER BY c.table_name, c.ordinal_position"""
    ).fetchall()
    tables: Schema = {}
    for r in rows:
        tables.setdefault(r["table_name"], []).append(r["column_name"])
    return tables


def shared_columns(local: Schema, remote: Schema, table: str) -> str:
    return ", ".join(c for c in local[table] if c in remote[table])


def tables_to_replace(local: Schema, remote: Schema) -> list[str]:
    return sorted(t for t in local.keys() & remote.keys() if t not in SKIPPED)


def differences(local: Schema, remote: Schema) -> list[str]:
    """How the two schemas differ; only shared tables and columns get copied."""
    notes = [f"table {t}: only local (not deployed yet?), not copied" for t in sorted(local.keys() - remote.keys())]
    notes += [f"table {t}: only in production (pull main?), not copied" for t in sorted(remote.keys() - local.keys())]
    for t in sorted(local.keys() & remote.keys()):
        notes += [f"{t}.{c}: only local, left empty" for c in local[t] if c not in remote[t]]
        notes += [f"{t}.{c}: only in production, not copied" for c in remote[t] if c not in local[t]]
    return notes


def copy(
    src: psycopg.Connection[Row], dst: psycopg.Connection[Row], table: str, cols: str, where: str = "", params=()
) -> int:
    """Stream the matching rows of a table from src into dst; returns how many were copied."""
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
    local_schema, remote_schema = schema(local), schema(remote)
    for note in differences(local_schema, remote_schema):
        print(f"schema drift: {note}")
    bars = shared_columns(local_schema, remote_schema, "daily_bars")

    local_max = one(local.execute("SELECT MAX(date) FROM daily_bars"))[0]
    with local.transaction():
        for table in tables_to_replace(local_schema, remote_schema):
            local.execute(f"DELETE FROM {table}")
            print(f"{table}: {copy(remote, local, table, shared_columns(local_schema, remote_schema, table))} rows")
        if local_max is None:
            print(f"daily_bars: {copy(remote, local, 'daily_bars', bars)} rows (full copy)")
        else:
            changed = changed_tickers(fingerprints(local, local_max), fingerprints(remote, local_max))
            if changed:
                local.execute("DELETE FROM daily_bars WHERE ticker = ANY(%s)", (changed,))
                recopied = copy(remote, local, "daily_bars", bars, "WHERE ticker = ANY(%s)", (changed,))
                print(f"daily_bars: {len(changed)} tickers re-copied ({recopied} rows): {', '.join(changed[:10])}"
                      + (" …" if len(changed) > 10 else ""))  # fmt: skip
            new = copy(remote, local, "daily_bars", bars, "WHERE date > %s AND NOT (ticker = ANY(%s))", (local_max, changed))
            print(f"daily_bars: +{new} rows after {local_max}")
    compute_rs(local)
    rated = one(local.execute("SELECT MAX(date) FROM rs_ratings"))[0]
    print(f"\nLocal is up to date with production through {rated}")


if __name__ == "__main__":
    main()
