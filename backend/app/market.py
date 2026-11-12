"""Market direction: the S&P 500 trend from the benchmark's 50- and 200-day moving averages,
plus breadth (the share of companies above their own 50-day average), shown for context only."""

from collections.abc import Sequence

import psycopg

from app.config import BENCHMARK

SHORT, LONG = 50, 200  # trading days
SLOPE_LOOKBACK = 10  # the 50-day average is rising if it's above its value this many days ago
MONTH, QUARTER = 21, 63

UPTREND, UNDER_PRESSURE, DOWNTREND = "Uptrend", "Under pressure", "Downtrend"


def moving_average(closes: Sequence[float], n: int, end: int | None = None) -> float | None:
    """Average of the n closes before index end (default: the last n)."""
    end = len(closes) if end is None else end
    if end < n:
        return None
    return sum(closes[end - n : end]) / n


def status(close: float, ma50: float, ma200: float, ma50_rising: bool) -> str:
    if close > ma50 > ma200:
        return UPTREND
    if close < ma200 and not ma50_rising:
        return DOWNTREND
    return UNDER_PRESSURE


def direction(closes: Sequence[float]) -> dict | None:
    """Market direction from benchmark closes ending on the rated date; None without 200 bars."""
    if len(closes) < LONG:
        return None
    close = closes[-1]
    ma50 = moving_average(closes, SHORT)
    ma200 = moving_average(closes, LONG)
    ma50_rising = ma50 > moving_average(closes, SHORT, len(closes) - SLOPE_LOOKBACK)
    return {
        "status": status(close, ma50, ma200, ma50_rising),
        "close": close,
        "ma50": ma50,
        "ma200": ma200,
        "ma50_rising": ma50_rising,
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


def market_direction(conn: psycopg.Connection, date: str) -> dict | None:
    """Market direction as of date, from daily_bars; None if the benchmark has under 200 bars."""
    bench = conn.execute(
        "SELECT date, close FROM daily_bars WHERE ticker = %s AND date <= %s ORDER BY date DESC LIMIT %s",
        (BENCHMARK, date, LONG),
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
