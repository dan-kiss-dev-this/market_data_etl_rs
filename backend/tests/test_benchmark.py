from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from app import main, rs

N = rs.MIN_BARS


class Cursor:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


@pytest.fixture
def client(monkeypatch):
    """The API over a fake database: SPY doubled over 12 months and gained 10% over 3, and isn't in companies."""
    closes = [50.0] * (N - 64) + [100.0] * 63 + [110.0]
    db = {"rated": "2026-11-26", "closes": closes}

    class Conn:
        def execute(self, sql, params=()):
            if "MAX(date) FROM rs_ratings" in sql:
                return Cursor([(db["rated"],)])
            if "FROM companies" in sql:
                return Cursor([])
            if "b.close / s.close" in sql:
                return Cursor([{"date": "2026-11-26", "close": 110.0, "rs_line": 1.0, "rs_rating": None}])
            if "FROM daily_bars" in sql:
                return Cursor([{"close": c} for c in db["closes"]])
            raise AssertionError(sql)

    class Pool:
        @contextmanager
        def connection(self):
            yield Conn()

    monkeypatch.setattr(main, "pool", lambda: Pool())
    return TestClient(main.app), db


def test_benchmark_has_its_close_and_returns_on_the_rated_date(client):
    api, _ = client
    res = api.get("/api/rs/benchmark")
    assert res.status_code == 200
    body = res.json()
    assert body["ticker"] == "SPY"
    assert body["date"] == "2026-11-26"
    assert body["close"] == 110.0
    assert body["ret_3m"] == pytest.approx(0.1)
    assert body["ret_12m"] == pytest.approx(1.2)


def test_benchmark_is_404_before_the_first_ratings(client):
    api, db = client
    db["rated"] = None
    assert api.get("/api/rs/benchmark").status_code == 404


def test_benchmark_has_a_price_series_though_it_is_not_a_company(client):
    api, _ = client
    res = api.get("/api/rs/spy")
    assert res.status_code == 200
    assert res.json()["ticker"] == "SPY"
    assert res.json()["series"][0]["close"] == 110.0


def test_unknown_tickers_are_still_404(client):
    api, _ = client
    assert api.get("/api/rs/ZZZZ").status_code == 404
