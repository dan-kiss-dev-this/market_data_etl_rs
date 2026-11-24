"""Market condition: Strong, Normal or Shaky market, from the benchmark's 50- and 200-day moving averages,
plus breadth (the share of companies above their own 50-day average), shown for context only.

Run with --backfill to recompute every stored market_directions row with the current rule."""

import argparse
from collections.abc import Sequence
from itertools import pairwise

import psycopg
from psycopg.types.json import Jsonb

from app.config import BENCHMARK
from app.db import Row, connect

SHORT, LONG = 50, 200  # trading days
SLOPE_LOOKBACK = 10  # the 50-day average is rising if it's above its value this many days ago
LONG_SLOPE_LOOKBACK = 20  # the same for the 200-day average
CROSSING_WINDOW = 20  # trading days in which failed 50-day crossings are counted
FAILED_CROSSINGS = 2  # this many while below the 50-day makes it a Shaky market
MIN_BARS = LONG + LONG_SLOPE_LOOKBACK
MONTH, QUARTER = 21, 63

STRONG, NORMAL, SHAKY = "Strong market", "Normal market", "Shaky market"


def moving_average(closes: Sequence[float], n: int, end: int | None = None) -> float | None:
    """Average of the n closes before index end (default: the last n)."""
    end = len(closes) if end is None else end
    if end < n:
        return None
    return sum(closes[end - n : end]) / n


def failed_crossings(closes: Sequence[float]) -> int:
    """Times in the last CROSSING_WINDOW trading days a close above the 50-day was followed by one below it."""
    n = len(closes)
    above = [closes[end - 1] > moving_average(closes, SHORT, end) for end in range(n - CROSSING_WINDOW, n + 1)]
    return sum(prev and not now for prev, now in pairwise(above))


def status(close: float, ma50: float, ma200: float, ma50_rising: bool, ma200_rising: bool, failed: int) -> str:
    if close < ma200 or (close < ma50 and (not ma50_rising or failed >= FAILED_CROSSINGS)):
        return SHAKY
    if close > ma50 > ma200 and ma50_rising and ma200_rising:
        return STRONG
    return NORMAL


def direction(closes: Sequence[float]) -> dict | None:
    """Market condition from benchmark closes ending on the rated date; None without MIN_BARS bars."""
    if len(closes) < MIN_BARS:
        return None
    close = closes[-1]
    ma50 = moving_average(closes, SHORT)
    ma200 = moving_average(closes, LONG)
    ma50_rising = ma50 > moving_average(closes, SHORT, len(closes) - SLOPE_LOOKBACK)
    ma200_rising = ma200 > moving_average(closes, LONG, len(closes) - LONG_SLOPE_LOOKBACK)
    failed = failed_crossings(closes)
    return {
        "status": status(close, ma50, ma200, ma50_rising, ma200_rising, failed),
        "close": close,
        "ma50": ma50,
        "ma200": ma200,
        "ma50_rising": ma50_rising,
        "ma200_rising": ma200_rising,
        "failed_50_day_crossings": failed,
        "ret_1m": close / closes[-1 - MONTH] - 1,
        "ret_3m": close / closes[-1 - QUARTER] - 1,
    }


def breadth(closes_by_ticker: dict[str, Sequence[float]]) -> float | None:
    """Share (0-1) of companies whose latest close is above their own 50-day average.
    Companies with fewer than 50 closes are left out."""
    above = counted = 0
    for closes in closes_by_ticker.values():
        ma50 = moving_average(closes, SHORT)
        if ma50 is None:
            continue
        counted += 1
        above += closes[-1] > ma50
    return above / counted if counted else None


def market_direction(conn: psycopg.Connection[Row], date: str) -> dict | None:
    """Market condition as of date, from daily_bars; None if the benchmark has under MIN_BARS bars."""
    bench = conn.execute(
        "SELECT date, close FROM daily_bars WHERE ticker = %s AND date <= %s ORDER BY date DESC LIMIT %s",
        (BENCHMARK, date, MIN_BARS),
    ).fetchall()[::-1]
    result = direction([r["close"] for r in bench])
    if result is None:
        return None
    # Only companies that traded on date, over the benchmark's last 50 trading days
    rows = conn.execute(
        """SELECT b.ticker, b.close FROM daily_bars b
           JOIN companies USING (ticker)
           WHERE b.date >= %s AND b.date <= %s
             AND b.ticker IN (SELECT ticker FROM daily_bars WHERE date = %s)
           ORDER BY b.ticker, b.date""",
        (bench[-SHORT]["date"], date, date),
    ).fetchall()
    closes_by_ticker: dict[str, list[float]] = {}
    for r in rows:
        closes_by_ticker.setdefault(r["ticker"], []).append(r["close"])
    return {"date": date, **result, "breadth": breadth(closes_by_ticker)}


def save_market(conn: psycopg.Connection[Row], market: dict) -> None:
    with conn.transaction():
        conn.execute(
            "INSERT INTO market_directions VALUES (%s, %s) ON CONFLICT (date) DO UPDATE SET data = EXCLUDED.data",
            (market["date"], Jsonb(market)),
        )


def backfill(conn: psycopg.Connection[Row]) -> None:
    """Recompute every stored date with the current rule; delete dates without enough history."""
    dates = [r["date"] for r in conn.execute("SELECT date FROM market_directions ORDER BY date").fetchall()]
    deleted = 0
    for date in dates:
        market = market_direction(conn, date)
        if market is None:
            with conn.transaction():
                conn.execute("DELETE FROM market_directions WHERE date = %s", (date,))
            deleted += 1
        else:
            save_market(conn, market)
    print(f"Recomputed {len(dates) - deleted} Market conditions, deleted {deleted} without {MIN_BARS} bars")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--backfill", action="store_true", help="recompute every stored market_directions row")
    args = parser.parse_args()
    if args.backfill:
        backfill(connect())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
