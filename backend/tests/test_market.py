import contextlib
import sys

import pytest

from app import market


def line(start: float, step: float, n: int = market.MIN_BARS) -> list[float]:
    return [start + step * i for i in range(n)]


def test_needs_220_bars():
    assert market.MIN_BARS == 220
    assert market.direction(line(100, 1, market.MIN_BARS - 1)) is None
    assert market.direction(line(100, 1)) is not None


def test_steady_rise_is_a_strong_market():
    result = market.direction(line(100, 1))
    assert result["status"] == market.STRONG
    assert result["ma50_rising"] and result["ma200_rising"]
    assert result["close"] > result["ma50"] > result["ma200"]
    assert result["failed_50_day_crossings"] == 0


def test_steady_fall_is_a_shaky_market():
    result = market.direction(line(500, -1))
    assert result["status"] == market.SHAKY
    assert not result["ma50_rising"]


def test_below_the_200_day_is_shaky_even_with_the_50_day_rising():
    # Long decline, then a recent rally lifts the 50-day while price is still under the 200-day
    closes = line(400, -1, 170) + line(230, 0.5, 50)
    result = market.direction(closes)
    assert result["close"] < result["ma200"]
    assert result["close"] > result["ma50"]
    assert result["ma50_rising"]
    assert result["status"] == market.SHAKY


def test_one_dip_below_a_rising_50_day_is_a_normal_market():
    # Rising for 215 days, then a sharp 5-day drop: below the 50-day, still above the 200-day
    closes = line(100, 1, 215) + [300, 296, 292, 288, 284]
    result = market.direction(closes)
    assert result["close"] < result["ma50"]
    assert result["close"] > result["ma200"]
    assert result["ma50_rising"]
    assert result["failed_50_day_crossings"] == 1
    assert result["status"] == market.NORMAL


def test_repeatedly_failing_at_the_50_day_is_a_shaky_market():
    # Rising, then it keeps closing back above the 50-day and falling under it again
    closes = line(100, 1, 210) + [280, 300, 280, 300, 280, 300, 280, 300, 280, 280]
    result = market.direction(closes)
    assert result["close"] < result["ma50"]
    assert result["close"] > result["ma200"]
    assert result["ma50_rising"]
    assert result["failed_50_day_crossings"] >= 2
    assert result["status"] == market.SHAKY


def test_failed_crossings_only_count_the_last_20_trading_days():
    # Two failures 30 days ago, then a clean rise back above the 50-day
    closes = line(100, 1, 180) + [250, 290, 250, 290, 250] + line(260, 2, 35)
    assert market.failed_crossings(closes) == 0


def test_a_falling_200_day_keeps_it_out_of_a_strong_market():
    # High closes 200-220 days ago are dropping out of the 200-day, so it falls while price rises
    closes = [1000.0] * market.LONG_SLOPE_LOOKBACK + line(100, 1, market.LONG)
    result = market.direction(closes)
    assert result["close"] > result["ma50"] > result["ma200"]
    assert result["ma50_rising"]
    assert not result["ma200_rising"]
    assert result["status"] == market.NORMAL


def test_flat_market_is_a_normal_market():
    assert market.direction([100.0] * market.MIN_BARS)["status"] == market.NORMAL


def test_returns_use_21_and_63_trading_days():
    closes = [100.0] * (market.MIN_BARS - market.QUARTER - 1) + [80.0] * (market.QUARTER - market.MONTH) + [90.0] * market.MONTH + [99.0]
    result = market.direction(closes)
    assert result["ret_1m"] == pytest.approx(99 / 90 - 1)
    assert result["ret_3m"] == pytest.approx(99 / 80 - 1)


def test_breadth_is_share_above_own_50_day():
    rising, falling = line(100, 1, 50), line(200, -1, 50)
    assert market.breadth({"A": rising, "B": rising, "C": falling, "D": falling}) == pytest.approx(0.5)


def test_breadth_skips_short_histories():
    assert market.breadth({"A": line(100, 1, 50), "NEW": [10.0] * 10}) == pytest.approx(1.0)
    assert market.breadth({"NEW": [10.0] * 10}) is None


class FakeConn:
    """Lists the stored market_directions dates and records deletes."""

    def __init__(self, dates: list[str]):
        self.dates = dates
        self.deleted: list[str] = []

    def execute(self, sql: str, params=None):
        if sql.lstrip().startswith("DELETE"):
            self.deleted.append(params[0])
        return self

    def fetchall(self):
        return [{"date": d} for d in self.dates]

    def transaction(self):
        return contextlib.nullcontext()


def test_backfill_recomputes_each_stored_date_and_deletes_short_histories(monkeypatch):
    conn = FakeConn(["2025-01-02", "2026-11-20", "2026-11-23"])
    saved = []
    monkeypatch.setattr(market, "market_direction", lambda conn, date: None if date == "2025-01-02" else {"date": date})
    monkeypatch.setattr(market, "save_market", lambda conn, m: saved.append(m["date"]))
    market.backfill(conn)
    assert saved == ["2026-11-20", "2026-11-23"]
    assert conn.deleted == ["2025-01-02"]


def test_main_runs_the_backfill(monkeypatch):
    calls = []
    monkeypatch.setattr(sys, "argv", ["market", "--backfill"])
    monkeypatch.setattr(market, "connect", lambda: "conn")
    monkeypatch.setattr(market, "backfill", calls.append)
    market.main()
    assert calls == ["conn"]
