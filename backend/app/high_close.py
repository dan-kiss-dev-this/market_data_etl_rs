"""The 2-year high close: each ticker's highest close in daily_bars, which holds about 2 years.

Rebuilt whole by every Daily refresh, since split adjustments and rename rebuilds rewrite past closes.
"""

from collections.abc import Iterable, Mapping

import psycopg

from app.db import Row

COLUMNS = ("ticker", "date", "close")


def highest_closes(bars: Iterable[Mapping]) -> list[tuple[str, str, float]]:
    """(ticker, date, close) of each ticker's highest close, by ticker; a tie keeps the latest date."""
    best: dict[str, tuple[float, str]] = {}
    for b in bars:
        if b["ticker"] not in best or (b["close"], b["date"]) > best[b["ticker"]]:
            best[b["ticker"]] = (b["close"], b["date"])
    return [(ticker, d, close) for ticker, (close, d) in sorted(best.items())]


def refresh_high_closes(conn: psycopg.Connection[Row]) -> None:
    rows = highest_closes(conn.execute("SELECT ticker, date, close FROM daily_bars"))
    with conn.transaction():
        conn.execute("DELETE FROM high_close_past_2_years")
        with conn.cursor().copy(f"COPY high_close_past_2_years ({', '.join(COLUMNS)}) FROM STDIN") as copy:
            for row in rows:
                copy.write_row(row)
    print(f"2-year high closes: {len(rows)} tickers")
