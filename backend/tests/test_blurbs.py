from contextlib import nullcontext
from datetime import UTC, date, datetime

import httpx
import pytest

from app import blurbs
from app.massive import MassiveClient

RATED = "2026-11-10"
TODAY = date(2026, 11, 12)


def utc(*args) -> datetime:
    return datetime(*args, tzinfo=UTC)


def test_refresh_window_blocks_tuesday_to_saturday_at_7_and_13_utc():
    assert blurbs.in_refresh_window(utc(2026, 11, 10, 7, 0))  # Tuesday
    assert blurbs.in_refresh_window(utc(2026, 11, 14, 13, 44))  # Saturday
    assert not blurbs.in_refresh_window(utc(2026, 11, 10, 7, 45))
    assert not blurbs.in_refresh_window(utc(2026, 11, 10, 8, 0))
    assert not blurbs.in_refresh_window(utc(2026, 11, 9, 7, 10))  # Monday: no refresh
    assert not blurbs.in_refresh_window(utc(2026, 11, 15, 13, 10))  # Sunday


def test_trading_days_behind_counts_weekdays_between():
    assert blurbs.trading_days_behind("2026-11-11", TODAY) == 0  # Wednesday's ratings on Thursday
    assert blurbs.trading_days_behind("2026-11-06", date(2026, 11, 10)) == 1  # Fri -> Tue: Monday missing
    assert blurbs.trading_days_behind("2026-11-05", TODAY) == 4


def test_more_than_10_failures_fails_the_run():
    assert not blurbs.too_many_failures(["T"] * 10)
    assert blurbs.too_many_failures(["T"] * 11)


def blurb(sources: list[int]) -> blurbs.Blurb:
    return blurbs.Blurb(
        what_they_sell="Chips.",
        catalyst="New GPU launch.",
        catalyst_sources=sources,
        category_position="Leader.",
        momentum="Strong.",
        risks="Export rules.",
    )


def headline(n: int) -> dict:
    return {"date": f"2026-11-0{n}", "title": f"H{n}", "publisher": "P", "url": f"u{n}", "sentiment": "positive", "insight": "i"}


def test_cited_headlines_keep_order_drop_repeats_and_bad_numbers_and_cap_at_3():
    news = [headline(n) for n in range(1, 6)]
    cited = blurbs.cited_headlines(blurb([4, 4, 0, 9, 2, 1, 5]), news)
    assert [h["title"] for h in cited] == ["H4", "H2", "H1"]
    assert blurbs.cited_headlines(blurb([]), news) == []


LEADER = {
    "ticker": "NVDA", "name": "Nvidia", "sector": "Information Technology", "rs_rating": 97,
    "rs_score": 180.0, "ret_3m": 0.25, "ret_12m": 0.8, "rs_new_high": True,
    "sector_rank": 2, "sector_size": 68, "rating_change_1w": 3,
}  # fmt: skip
MARKET = {"date": RATED, "status": "Under pressure", "close": 749.9, "ma50": 765.0, "ma200": 731.0,
          "ma50_rising": False, "ret_1m": -0.036, "ret_3m": -0.029, "breadth": 0.69}  # fmt: skip


def test_prompt_numbers_headlines_and_includes_rs_and_market():
    prompt = blurbs.build_prompt(LEADER, RATED, "Makes GPUs.", [headline(1), headline(2)], MARKET)
    assert "[1] 2026-11-01 · P · H1" in prompt
    assert "[2] 2026-11-02" in prompt
    assert "RS rating 97 (1-week change: +3), rank 2 of 68" in prompt
    assert "3-month return +25.0%" in prompt
    assert "Under pressure. The S&P 500 is below its 50-day average, which is falling" in prompt
    assert "69% of S&P 500 companies" in prompt


def test_prompt_without_news_market_or_history():
    leader = {**LEADER, "rating_change_1w": None}
    prompt = blurbs.build_prompt(leader, RATED, "", [], None)
    assert "Description: Not available." in prompt
    assert "1-week change: n/a" in prompt
    assert "Market direction: Not available." in prompt
    assert "None." in prompt


class FakeConn:
    """Answers company_profiles lookups with one stored row and records writes."""

    def __init__(self, profile: dict | None = None):
        self.profile = profile
        self.writes: list[tuple] = []

    def execute(self, sql: str, params=None):
        if sql.lstrip().startswith("INSERT"):
            self.writes.append(params)
        return self

    def fetchone(self):
        return self.profile

    def transaction(self):
        return nullcontext()


class FakeMassive:
    def __init__(self, fail: set[str] = frozenset()):
        self.fail = fail
        self.details_calls: list[str] = []

    def ticker_details(self, ticker: str) -> dict:
        self.details_calls.append(ticker)
        return {"description": f"{ticker} description"}

    def ticker_news(self, ticker, since, until, limit):
        if ticker in self.fail:
            raise httpx.HTTPError("boom")
        return [headline(1)]


def test_recent_description_is_reused():
    conn, massive = FakeConn({"description": "Saved.", "fetched_at": "2026-09-01"}), FakeMassive()
    assert blurbs.company_description(conn, massive, "NVDA", TODAY) == "Saved."
    assert massive.details_calls == []


def test_description_over_90_days_old_is_refetched_and_saved():
    conn, massive = FakeConn({"description": "Old.", "fetched_at": "2026-08-01"}), FakeMassive()
    assert blurbs.company_description(conn, massive, "NVDA", TODAY) == "NVDA description"
    assert conn.writes == [("NVDA", "NVDA description", "2026-11-12")]


def test_missing_description_is_fetched():
    conn, massive = FakeConn(None), FakeMassive()
    assert blurbs.company_description(conn, massive, "NVDA", TODAY) == "NVDA description"
    assert massive.details_calls == ["NVDA"]


@pytest.fixture
def no_db(monkeypatch):
    """Run the Blurb run loop with the database calls replaced; returns the saved Blurbs."""
    saved: list[tuple] = []
    monkeypatch.setattr(blurbs, "market_direction", lambda conn, rated: MARKET)
    monkeypatch.setattr(blurbs, "save_market", lambda conn, market: None)
    monkeypatch.setattr(blurbs, "company_description", lambda conn, client, ticker, today: "desc")
    monkeypatch.setattr(blurbs, "save_blurb", lambda conn, ticker, rated, b, headlines: saved.append((ticker, headlines)))
    monkeypatch.setattr(blurbs, "write_blurb", lambda ai, prompt: blurb([1]))
    return saved


def test_failed_leader_is_skipped_and_the_rest_are_saved(no_db):
    leaders = [{**LEADER, "ticker": t} for t in ("AAA", "BBB", "CCC")]
    skipped = blurbs.run(None, FakeMassive(fail={"BBB"}), None, RATED, TODAY, leaders)
    assert skipped == ["BBB"]
    assert [t for t, _ in no_db] == ["AAA", "CCC"]
    assert no_db[0][1] == [headline(1)]


def test_refused_blurb_is_skipped(no_db, monkeypatch):
    def refuse(ai, prompt):
        raise blurbs.BlurbError("model stopped with refusal")

    monkeypatch.setattr(blurbs, "write_blurb", refuse)
    assert blurbs.run(None, FakeMassive(), None, RATED, TODAY, [LEADER]) == ["NVDA"]
    assert no_db == []


def news_client(articles: list[dict]) -> MassiveClient:
    client = MassiveClient.__new__(MassiveClient)
    client._get = lambda url, params=None: {"results": articles}
    return client


def article(day: int, tickers: list[str], insight_for: str | None = "NVDA") -> dict:
    insights = [{"ticker": insight_for, "sentiment": "positive", "sentiment_reasoning": "why"}] if insight_for else []
    return {
        "published_utc": f"2026-11-{day:02d}T12:00:00Z", "title": f"T{day}", "article_url": f"u{day}",
        "publisher": {"name": "P"}, "tickers": tickers, "insights": insights,
    }  # fmt: skip


def test_ticker_news_keeps_focused_articles_about_the_ticker_oldest_first():
    articles = [  # newest first, as Massive returns them
        article(9, ["NVDA", "A", "B", "C", "D", "E"]),  # mentions too many tickers
        article(8, ["NVDA", "AMD"], insight_for="AMD"),  # no insight about NVDA
        article(7, ["NVDA", "AMD", "TSM"]),
        article(6, ["NVDA"]),
        article(5, ["NVDA"]),
    ]
    news = news_client(articles).ticker_news("NVDA", "2026-10-11", RATED, limit=2)
    # The two single-ticker articles win over the 3-ticker one, then go oldest first
    assert [a["title"] for a in news] == ["T5", "T6"]
    assert news[0] == {"date": "2026-11-05", "title": "T5", "publisher": "P", "url": "u5", "sentiment": "positive", "insight": "why"}


def test_blurb_is_current_for_7_days_after_its_rated_date():
    from app.main import is_current

    assert is_current("2026-11-05", TODAY)
    assert not is_current("2026-11-04", TODAY)
