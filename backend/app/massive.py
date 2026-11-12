import time
from datetime import UTC, date, datetime

import httpx

from app.config import MASSIVE_API_KEY, MASSIVE_BASE_URL

# Free tier allows 5 calls per minute
MIN_SECONDS_BETWEEN_CALLS = 12.5
# One news call fetches this many articles, which ticker_news filters down
NEWS_FETCH_LIMIT = 50
MAX_TICKERS_PER_ARTICLE = 5


def bar_date(bar: dict) -> str:
    """Massive bar timestamps are ms since epoch at the start of the trading day."""
    return datetime.fromtimestamp(bar["t"] / 1000, tz=UTC).date().isoformat()


class MassiveClient:
    def __init__(self) -> None:
        if not MASSIVE_API_KEY:
            raise SystemExit("MASSIVE_API_KEY is missing; add it to backend/.env")
        # Bearer header keeps the key out of URLs and logs
        self._http = httpx.Client(
            base_url=MASSIVE_BASE_URL,
            headers={"Authorization": f"Bearer {MASSIVE_API_KEY}"},
            timeout=60,
        )
        self._last_call = 0.0

    def _get(self, url: str, params: dict | None = None) -> dict:
        while True:
            wait = self._last_call + MIN_SECONDS_BETWEEN_CALLS - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last_call = time.monotonic()
            resp = self._http.get(url, params=params)
            if resp.status_code == 429:
                print("  rate limited, waiting 60s")
                time.sleep(60)
                continue
            resp.raise_for_status()
            return resp.json()

    def grouped_daily(self, day: str) -> list[dict]:
        """Every US stock's bar for one trading day."""
        data = self._get(
            f"/v2/aggs/grouped/locale/us/market/stocks/{day}", {"adjusted": "true"}
        )
        return data.get("results") or []

    def ticker_daily(self, ticker: str, start: str, end: str) -> list[dict]:
        data = self._get(
            f"/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}",
            {"adjusted": "true", "sort": "asc", "limit": 50000},
        )
        return data.get("results") or []

    def ticker_events(self, ticker: str) -> list[tuple[str, str]]:
        """(date, symbol) pairs: from each date on, the company traded under that symbol."""
        try:
            data = self._get(f"/vX/reference/tickers/{ticker}/events", {"types": "ticker_change"})
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []
            raise
        events = (data.get("results") or {}).get("events") or []
        return sorted((e["date"], e["ticker_change"]["ticker"]) for e in events)

    def ticker_details(self, ticker: str) -> dict:
        """Massive's reference data for a ticker, including its company description."""
        try:
            data = self._get(f"/v3/reference/tickers/{ticker}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {}
            raise
        return data.get("results") or {}

    def ticker_news(self, ticker: str, since: str, until: str, limit: int = 10) -> list[dict]:
        """Up to `limit` articles about ticker published from since to until (dates), oldest first.
        Massive tags an article with every ticker it mentions, so keep only articles with an
        insight about this ticker that mention a few tickers at most, preferring the most focused."""
        data = self._get(
            "/v2/reference/news",
            {
                "ticker": ticker,
                "published_utc.gte": since,
                "published_utc.lte": f"{until}T23:59:59Z",
                "sort": "published_utc",
                "order": "desc",
                "limit": NEWS_FETCH_LIMIT,
            },
        )
        focused = []
        for article in data.get("results") or []:
            insight = next((i for i in article.get("insights") or [] if i.get("ticker") == ticker), None)
            mentions = len(article.get("tickers") or [])
            if insight is None or mentions > MAX_TICKERS_PER_ARTICLE:
                continue
            focused.append(
                (
                    mentions,
                    {
                        "date": article["published_utc"][:10],
                        "title": article["title"],
                        "publisher": (article.get("publisher") or {}).get("name", ""),
                        "url": article["article_url"],
                        "sentiment": insight.get("sentiment", ""),
                        "insight": insight.get("sentiment_reasoning", ""),
                    },
                )
            )
        # Stable sort keeps newest first among articles equally focused
        focused.sort(key=lambda m: m[0])
        return sorted((a for _, a in focused[:limit]), key=lambda a: a["date"])

    def splits(self, since: str, until: str | None = None) -> list[dict]:
        """Splits executed between since and until (default today); follows pagination."""
        params: dict | None = {
            "execution_date.gte": since,
            "execution_date.lte": until or date.today().isoformat(),
            "limit": 5000,
        }
        url = "/stocks/v1/splits"
        results: list[dict] = []
        while url:
            data = self._get(url, params)
            results.extend(data.get("results") or [])
            # next_url already carries the cursor and filters
            url, params = data.get("next_url"), None
        return results
