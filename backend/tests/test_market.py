import pytest

from app import market


def line(start: float, step: float, n: int = market.LONG) -> list[float]:
    return [start + step * i for i in range(n)]


def test_needs_200_bars():
    assert market.direction(line(100, 1, market.LONG - 1)) is None
    assert market.direction(line(100, 1)) is not None


def test_steady_rise_is_uptrend():
    result = market.direction(line(100, 1))
    assert result["status"] == market.UPTREND
    assert result["ma50_rising"]
    assert result["close"] > result["ma50"] > result["ma200"]


def test_steady_fall_is_downtrend():
    result = market.direction(line(400, -1))
    assert result["status"] == market.DOWNTREND
    assert not result["ma50_rising"]


def test_dip_below_50_day_in_an_uptrend_is_under_pressure():
    # Rising for 195 days, then a sharp 5-day drop: below the 50-day, still above the 200-day
    closes = line(100, 1, 195) + [260, 255, 250, 245, 240]
    result = market.direction(closes)
    assert result["close"] < result["ma50"]
    assert result["close"] > result["ma200"]
    assert result["status"] == market.UNDER_PRESSURE


def test_below_200_day_with_50_day_still_rising_is_under_pressure():
    # Long decline, then a recent rally lifts the 50-day while price is still under the 200-day
    closes = line(400, -1, 150) + line(250, 0.5, 50)
    result = market.direction(closes)
    assert result["close"] < result["ma200"]
    assert result["ma50_rising"]
    assert result["status"] == market.UNDER_PRESSURE


def test_flat_market_is_under_pressure():
    assert market.direction([100.0] * market.LONG)["status"] == market.UNDER_PRESSURE


def test_returns_use_21_and_63_trading_days():
    closes = [100.0] * (market.LONG - market.QUARTER - 1) + [80.0] * (market.QUARTER - market.MONTH) + [90.0] * market.MONTH + [99.0]
    result = market.direction(closes)
    assert result["ret_1m"] == pytest.approx(99 / 90 - 1)
    assert result["ret_3m"] == pytest.approx(99 / 80 - 1)


def test_breadth_is_share_above_own_50_day():
    rising, falling = line(100, 1, 50), line(200, -1, 50)
    assert market.breadth({"A": rising, "B": rising, "C": falling, "D": falling}) == pytest.approx(0.5)


def test_breadth_skips_short_histories():
    assert market.breadth({"A": line(100, 1, 50), "NEW": [10.0] * 10}) == pytest.approx(1.0)
    assert market.breadth({"NEW": [10.0] * 10}) is None
