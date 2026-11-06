from functools import cache

import psycopg
from psycopg_pool import ConnectionPool

from app.config import DATABASE_URL

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
"""


class Row(tuple):
    """A result row readable by position or column name, like a tuple or a dict."""

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


def row_factory(cursor: psycopg.Cursor):
    names = [c.name for c in cursor.description or []]
    return lambda values: Row(names, values)


# autocommit: writes are grouped explicitly with conn.transaction(); without it the first
# read opens a hidden transaction and those blocks become savepoints that never commit.
# prepare_threshold=None: Supabase's transaction pooler can't handle prepared statements.
CONNECT_KWARGS = {"row_factory": row_factory, "autocommit": True, "prepare_threshold": None}


def connect() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL, **CONNECT_KWARGS)


def init_schema(conn: psycopg.Connection) -> None:
    with conn.transaction():
        conn.execute(SCHEMA)


@cache
def pool() -> ConnectionPool:
    """Shared connections for the API, so each request doesn't open a new one."""
    return ConnectionPool(DATABASE_URL, kwargs=CONNECT_KWARGS, min_size=1, max_size=5, open=True)
