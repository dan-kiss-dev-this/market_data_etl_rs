import sys

from app import etl, high_close, pull_prod


def bar(ticker: str, date: str, close: float) -> dict:
    return {"ticker": ticker, "date": date, "close": close}


def test_each_ticker_keeps_its_highest_close_and_date():
    bars = [
        bar("NVDA", "2025-01-02", 140.0), bar("NVDA", "2025-07-10", 239.24), bar("NVDA", "2026-11-13", 190.0),
        bar("AAPL", "2026-03-04", 250.5), bar("AAPL", "2025-12-01", 199.0),
    ]  # fmt: skip
    assert high_close.highest_closes(bars) == [("AAPL", "2026-03-04", 250.5), ("NVDA", "2025-07-10", 239.24)]


def test_a_tie_keeps_the_latest_date():
    bars = [bar("MSFT", "2025-05-01", 500.0), bar("MSFT", "2026-02-02", 500.0), bar("MSFT", "2025-09-09", 450.0)]
    assert high_close.highest_closes(bars) == [("MSFT", "2026-02-02", 500.0)]


def test_no_bars_means_no_rows():
    assert high_close.highest_closes([]) == []


def test_the_daily_refresh_rebuilds_high_closes_after_rs(monkeypatch):
    steps = []
    monkeypatch.setattr(sys, "argv", ["etl", "--rs-only"])
    monkeypatch.setattr(etl, "connect", lambda: None)
    monkeypatch.setattr(etl, "ensure_schema", lambda conn: None)
    for name in ("compute_rs", "refresh_high_closes", "update_market_direction", "print_summary"):
        monkeypatch.setattr(etl, name, lambda conn, name=name: steps.append(name))
    etl.main()
    assert steps == ["compute_rs", "refresh_high_closes", "update_market_direction", "print_summary"]


def test_pull_prod_rebuilds_the_table_locally_instead_of_copying_it():
    assert "high_close_past_2_years" in pull_prod.SKIPPED
    assert pull_prod.refresh_high_closes is high_close.refresh_high_closes
