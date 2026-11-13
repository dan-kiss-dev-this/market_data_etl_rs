import re
from datetime import UTC, datetime
from functools import cache
from urllib.parse import urlparse

import psycopg
from psycopg.rows import RowMaker
from psycopg_pool import ConnectionPool

from app.config import DATABASE_URL

# New tables go here. Changes to a table that already exists go in MIGRATIONS, since
# CREATE TABLE IF NOT EXISTS skips existing tables.
SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    ticker TEXT PRIMARY KEY,
    name   TEXT NOT NULL,
    sector TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS daily_bars (
    ticker TEXT NOT NULL,
    date   TEXT NOT NULL,
    close  DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (ticker, date)
);
-- One row per weekday we've asked Massive about; holidays are stored with rows = 0
CREATE TABLE IF NOT EXISTS fetched_dates (
    date       TEXT PRIMARY KEY,
    rows       INTEGER NOT NULL,
    fetched_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS splits_applied (
    ticker         TEXT NOT NULL,
    execution_date TEXT NOT NULL,
    PRIMARY KEY (ticker, execution_date)
);
-- Tickers whose history we've already rebuilt across old symbols (renames)
CREATE TABLE IF NOT EXISTS history_checked (
    ticker     TEXT PRIMARY KEY,
    checked_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rs_ratings (
    date        TEXT NOT NULL,
    ticker      TEXT NOT NULL,
    rs_score    DOUBLE PRECISION NOT NULL,
    rs_rating   INTEGER NOT NULL,
    ret_3m      DOUBLE PRECISION NOT NULL,
    ret_12m     DOUBLE PRECISION NOT NULL,
    rs_new_high BOOLEAN NOT NULL,
    PRIMARY KEY (date, ticker)
);
CREATE INDEX IF NOT EXISTS idx_rs_ratings_ticker ON rs_ratings (ticker, date);
-- Massive's company descriptions; kept apart from companies, which the ETL rebuilds each run
CREATE TABLE IF NOT EXISTS company_profiles (
    ticker      TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    fetched_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS market_directions (
    date TEXT PRIMARY KEY,
    data JSONB NOT NULL
);
-- One Blurb per Leader per rated date; headlines holds only the ones the Catalyst cites
CREATE TABLE IF NOT EXISTS blurbs (
    ticker     TEXT NOT NULL,
    date       TEXT NOT NULL,
    blurb      JSONB NOT NULL,
    headlines  JSONB NOT NULL,
    model      TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (ticker, date)
);
-- Chat messages sent per visitor per UTC day; the visitor '*' row holds the site total
CREATE TABLE IF NOT EXISTS chat_usage (
    day      TEXT NOT NULL,
    visitor  TEXT NOT NULL,
    messages INTEGER NOT NULL,
    PRIMARY KEY (day, visitor)
);
-- The MIGRATIONS versions this database has applied
CREATE TABLE IF NOT EXISTS schema_migrations (
    version    INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);
"""

# Changes to existing tables, applied once per database in this order; a migration's version is
# its position, counting from 1. Append only: never edit or reorder one that has shipped. Only
# additive changes (ADD COLUMN, CREATE INDEX); tests reject DROP, TRUNCATE, DELETE and type changes.
MIGRATIONS: list[str] = []

SCHEMA_TABLES = re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", SCHEMA)
SCHEMA_LOCK = 7_310_001  # pg_advisory_xact_lock key, so two processes never migrate at once
LOCAL_HOSTS = {None, "", "localhost", "127.0.0.1", "::1"}  # None: a Unix socket


class Row(tuple):
    """A result row readable by position or column name, like a tuple or a dict."""

    _index: dict[str, int]

    def __new__(cls, names: list[str], values):
        row = super().__new__(cls, values)
        row._index = {n: i for i, n in enumerate(names)}
        return row

    def __getitem__(self, key):
        if isinstance(key, str):
            key = self._index[key]
        return super().__getitem__(key)

    def keys(self) -> list[str]:
        return list(self._index)


def row_factory(cursor: psycopg.Cursor) -> RowMaker[Row]:
    names = [c.name for c in cursor.description or []]
    return lambda values: Row(names, values)


# autocommit: writes are grouped explicitly with conn.transaction(); without it the first
# read opens a hidden transaction and those blocks become savepoints that never commit.
# prepare_threshold=None: Supabase's transaction pooler can't handle prepared statements.
CONNECT_KWARGS = {"row_factory": row_factory, "autocommit": True, "prepare_threshold": None}


def connect() -> psycopg.Connection[Row]:
    # Connection[Row].connect rather than psycopg.connect, which type checkers read as yielding tuples
    return psycopg.Connection[Row].connect(DATABASE_URL, **CONNECT_KWARGS)


def one(cursor: psycopg.Cursor[Row]) -> Row:
    """The row of a query that always returns exactly one, such as SELECT MAX(...)."""
    row = cursor.fetchone()
    if row is None:
        raise LookupError("expected one row, got none")
    return row


def is_local(url: str) -> bool:
    return urlparse(url).hostname in LOCAL_HOSTS


def tables(conn: psycopg.Connection[Row]) -> set[str]:
    rows = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
    ).fetchall()
    return {r["table_name"] for r in rows}


def applied_migrations(conn: psycopg.Connection[Row]) -> set[int]:
    return {r["version"] for r in conn.execute("SELECT version FROM schema_migrations")}


def pending(applied: set[int], count: int) -> list[int]:
    """The migration versions, out of the first `count`, not applied yet."""
    return [v for v in range(1, count + 1) if v not in applied]


def schema_gaps(existing: set[str], applied: set[int]) -> list[str]:
    """What a database is missing compared with this code: tables, then migrations."""
    return [f"table {t}" for t in SCHEMA_TABLES if t not in existing] + [
        f"migration {v}" for v in pending(applied, len(MIGRATIONS))
    ]


def init_schema(conn: psycopg.Connection[Row]) -> None:
    """Create missing tables and apply pending migrations, all or nothing."""
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(%s)", (SCHEMA_LOCK,))
        conn.execute(SCHEMA)
        for version in pending(applied_migrations(conn), len(MIGRATIONS)):
            conn.execute(MIGRATIONS[version - 1])
            conn.execute(
                "INSERT INTO schema_migrations VALUES (%s, %s)", (version, datetime.now(UTC).isoformat(timespec="seconds"))
            )


def ensure_schema(conn: psycopg.Connection[Row]) -> None:
    """Bring local Postgres up to date; anywhere else (Supabase), only check.

    Production's schema changes only when the API starts on Render, which deploys after tests pass.
    The Daily refresh runs whatever is on main, tested or not, so it must not change the schema.
    """
    if is_local(DATABASE_URL):
        init_schema(conn)
        return
    existing = tables(conn)
    gaps = schema_gaps(existing, applied_migrations(conn) if "schema_migrations" in existing else set())
    if gaps:
        raise SystemExit(
            f"The database is behind this code ({', '.join(gaps)}). "
            "It updates when the Render deploy finishes, which starts once the tests pass."
        )


@cache
def pool() -> ConnectionPool[psycopg.Connection[Row]]:
    """Shared connections for the API, so each request doesn't open a new one."""
    return ConnectionPool(DATABASE_URL, kwargs=CONNECT_KWARGS, min_size=1, max_size=5, open=True)
