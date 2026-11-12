"""Blurb run: write a Blurb for each Leader explaining why it's leading, from its company
description, RS data, recent news and the Market direction. Run by hand, about weekly.

Run from backend/:  uv run python -m app.blurbs [--limit N] [--ticker T] [--force]
Writes to whatever DATABASE_URL points at; set it to the production database to publish.
"""

import argparse
import sys
from datetime import UTC, date, datetime, timedelta

import anthropic
import httpx
import psycopg
from psycopg.types.json import Jsonb
from pydantic import BaseModel, ValidationError

from app.config import ANTHROPIC_API_KEY, BLURB_MODEL, LEADER_COUNT
from app.db import Row, connect, init_schema, one
from app.etl import weekdays
from app.market import market_direction
from app.massive import MassiveClient

# The Daily refresh starts at 07:00 and 13:00 UTC, Tuesday to Saturday, and shares the
# Massive key's 5-calls-a-minute limit; give each run 45 minutes to finish
REFRESH_HOURS_UTC = (7, 13)
REFRESH_WEEKDAYS = range(1, 6)  # Monday is 0
REFRESH_MINUTES = 45
NEWS_DAYS = 30
MAX_HEADLINES = 10
MAX_CITED = 3
DESCRIPTION_MAX_AGE = timedelta(days=90)
STALE_TRADING_DAYS = 3
MAX_FAILURES = 10
RED, RESET = "\033[31m", "\033[0m"

SYSTEM_PROMPT = """You write Blurbs for a momentum trading site. A Blurb explains, in a few lines, why a \
Leader (one of the 50 highest RS-rated S&P 500 companies) is leading. The site's thesis is that the \
best momentum stocks combine high relative strength with innovative new products and leadership of \
their category.

You get the company's description, its RS data, numbered news headlines from the last 30 days with \
Massive's per-company insight on each, and the Market direction.

Write each field in one or two plain sentences:
- what_they_sell: what the company sells and to whom. You may use general knowledge.
- catalyst: the specific, dated event in the headlines that best explains the move, such as a product \
launch, an earnings beat or raised guidance, a major contract or a regulatory approval. A plain analyst \
rating change is not a Catalyst. Use only the headlines given, never general knowledge. If none \
qualifies, write exactly "No clear Catalyst in recent news."
- catalyst_sources: the numbers of the headlines the catalyst relies on, at most 3; empty if there is \
no clear Catalyst.
- category_position: whether the company leads or follows in its product category (for example \
analog chips or pharmaceutical distribution), and against which rivals. Use general knowledge, not \
the RS data: a sector rank is not a category position.
- momentum: what the RS data says about the strength and freshness of the move, including its rank \
in its sector. The site already shows the Market direction, so don't restate it or add a general \
warning about it. Mention it only when the stock is clearly acting differently from the market, \
such as an RS new high while the market is Under pressure or in a Downtrend.
- risks: the main thing that could break the thesis.

Be concrete and plain. No hype, no advice to buy or sell."""


class Blurb(BaseModel):
    what_they_sell: str
    catalyst: str
    catalyst_sources: list[int]
    category_position: str
    momentum: str
    risks: str


class BlurbError(Exception):
    pass


def in_refresh_window(now: datetime) -> bool:
    """True while a Daily refresh is probably running (now is in UTC)."""
    return now.weekday() in REFRESH_WEEKDAYS and now.hour in REFRESH_HOURS_UTC and now.minute < REFRESH_MINUTES


def trading_days_behind(rated: str, today: date) -> int:
    """Weekdays after the rated date and before today that have no ratings (holidays count too)."""
    return len(weekdays(date.fromisoformat(rated) + timedelta(days=1), today - timedelta(days=1)))


def load_leaders(conn: psycopg.Connection[Row], rated: str, limit: int = LEADER_COUNT) -> list[dict]:
    """The Leaders on the rated date, ordered like /api/rs/leaders, with their rank in their sector."""
    prev = conn.execute(
        "SELECT DISTINCT date FROM rs_ratings WHERE date < %s ORDER BY date DESC LIMIT 1 OFFSET 4", (rated,)
    ).fetchone()
    rows = conn.execute(
        """WITH ranked AS (
               SELECT r.ticker, c.name, c.sector, r.rs_rating, r.rs_score, r.ret_3m, r.ret_12m, r.rs_new_high,
                      RANK() OVER (PARTITION BY c.sector ORDER BY r.rs_rating DESC, r.rs_score DESC) AS sector_rank,
                      COUNT(*) OVER (PARTITION BY c.sector) AS sector_size
               FROM rs_ratings r JOIN companies c USING (ticker)
               WHERE r.date = %(rated)s
           )
           SELECT ranked.*, ranked.rs_rating - p.rs_rating AS rating_change_1w
           FROM ranked
           LEFT JOIN rs_ratings p ON p.ticker = ranked.ticker AND p.date = %(prev)s
           ORDER BY ranked.rs_rating DESC, ranked.rs_score DESC
           LIMIT %(limit)s""",
        {"rated": rated, "prev": prev[0] if prev else None, "limit": limit},
    ).fetchall()
    return [dict(r) for r in rows]


def company_description(conn: psycopg.Connection[Row], client: MassiveClient, ticker: str, today: date) -> str:
    """The saved description, re-fetched from Massive when missing or over 90 days old."""
    row = conn.execute("SELECT description, fetched_at FROM company_profiles WHERE ticker = %s", (ticker,)).fetchone()
    if row and date.fromisoformat(row["fetched_at"]) > today - DESCRIPTION_MAX_AGE:
        return row["description"]
    description = client.ticker_details(ticker).get("description") or ""
    with conn.transaction():
        conn.execute(
            """INSERT INTO company_profiles VALUES (%s, %s, %s)
               ON CONFLICT (ticker) DO UPDATE SET description = EXCLUDED.description, fetched_at = EXCLUDED.fetched_at""",
            (ticker, description, today.isoformat()),
        )
    return description


def pct(x: float) -> str:
    return f"{x * 100:+.1f}%"


def describe_market(market: dict | None) -> str:
    if market is None:
        return "Not available."
    side = "above" if market["close"] > market["ma50"] else "below"
    trend = "rising" if market["ma50_rising"] else "falling"
    breadth = "n/a" if market["breadth"] is None else f"{market['breadth'] * 100:.0f}%"
    return (
        f"{market['status']}. The S&P 500 is {side} its 50-day average, which is {trend}; "
        f"1-month {pct(market['ret_1m'])}, 3-month {pct(market['ret_3m'])}; "
        f"{breadth} of S&P 500 companies are above their own 50-day average."
    )


def build_prompt(leader: dict, rated: str, description: str, news: list[dict], market: dict | None) -> str:
    change = leader["rating_change_1w"]
    headlines = "\n".join(
        f"[{i}] {a['date']} · {a['publisher']} · {a['title']}\n    Insight ({a['sentiment']}): {a['insight']}"
        for i, a in enumerate(news, 1)
    )
    return f"""Company: {leader['name']} ({leader['ticker']}), sector: {leader['sector']}
Description: {description or 'Not available.'}

RS data as of {rated}:
- RS rating {leader['rs_rating']} (1-week change: {'n/a' if change is None else f'{change:+d}'}), \
rank {leader['sector_rank']} of {leader['sector_size']} in its sector
- RS line at a new high: {'yes' if leader['rs_new_high'] else 'no'}
- 3-month return {pct(leader['ret_3m'])}, 12-month return {pct(leader['ret_12m'])}

Market direction: {describe_market(market)}

Headlines from the 30 days to {rated}:
{headlines or 'None.'}"""


def write_blurb(ai: anthropic.Anthropic, prompt: str) -> Blurb:
    response = ai.messages.parse(
        model=BLURB_MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
        output_format=Blurb,
        output_config={"effort": "low"},
    )
    if response.stop_reason != "end_turn" or response.parsed_output is None:
        raise BlurbError(f"model stopped with {response.stop_reason}")
    return response.parsed_output


def cited_headlines(blurb: Blurb, news: list[dict]) -> list[dict]:
    """The headlines the Catalyst cites, in citation order, without repeats or bad numbers."""
    numbers = [n for n in dict.fromkeys(blurb.catalyst_sources) if 1 <= n <= len(news)]
    return [news[n - 1] for n in numbers[:MAX_CITED]]


def too_many_failures(skipped: list[str]) -> bool:
    return len(skipped) > MAX_FAILURES


def save_blurb(conn: psycopg.Connection[Row], ticker: str, rated: str, blurb: Blurb, headlines: list[dict]) -> None:
    with conn.transaction():
        conn.execute(
            """INSERT INTO blurbs VALUES (%s, %s, %s, %s, %s, %s)
               ON CONFLICT (ticker, date) DO UPDATE SET blurb = EXCLUDED.blurb, headlines = EXCLUDED.headlines,
                   model = EXCLUDED.model, created_at = EXCLUDED.created_at""",
            (
                ticker,
                rated,
                Jsonb(blurb.model_dump(exclude={"catalyst_sources"})),
                Jsonb(headlines),
                BLURB_MODEL,
                datetime.now(UTC).isoformat(timespec="seconds"),
            ),
        )


def save_market(conn: psycopg.Connection[Row], market: dict) -> None:
    with conn.transaction():
        conn.execute(
            "INSERT INTO market_directions VALUES (%s, %s) ON CONFLICT (date) DO UPDATE SET data = EXCLUDED.data",
            (market["date"], Jsonb(market)),
        )


def run(
    conn: psycopg.Connection[Row],
    massive: MassiveClient,
    ai: anthropic.Anthropic,
    rated: str,
    today: date,
    leaders: list[dict],
) -> list[str]:
    """Write a Blurb for each Leader; returns the tickers that were skipped."""
    market = market_direction(conn, rated)
    if market is not None:
        save_market(conn, market)
    print(f"Market direction on {rated}: {market['status'] if market else 'not enough history'}")

    since = (date.fromisoformat(rated) - timedelta(days=NEWS_DAYS)).isoformat()
    skipped = []
    for n, leader in enumerate(leaders, 1):
        ticker = leader["ticker"]
        try:
            description = company_description(conn, massive, ticker, today)
            news = massive.ticker_news(ticker, since, rated, MAX_HEADLINES)
            blurb = write_blurb(ai, build_prompt(leader, rated, description, news, market))
        # A bad key or model name would fail every Leader, so stop instead of skipping
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError, anthropic.NotFoundError):
            raise
        except (httpx.HTTPError, anthropic.APIError, BlurbError, ValidationError) as e:
            print(f"  [{n}/{len(leaders)}] {ticker}: skipped ({e})")
            skipped.append(ticker)
            continue
        save_blurb(conn, ticker, rated, blurb, cited_headlines(blurb, news))
        print(f"  [{n}/{len(leaders)}] {ticker}: {blurb.catalyst}")
    return skipped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limit", type=int, default=LEADER_COUNT, help="only the first N Leaders")
    parser.add_argument("--ticker", help="only this Leader")
    parser.add_argument("--force", action="store_true", help="run even while a Daily refresh may be running")
    args = parser.parse_args()

    if in_refresh_window(datetime.now(UTC)) and not args.force:
        print(
            f"{RED}The Daily refresh is probably using Massive right now (it starts at 07:00 and 13:00 UTC, "
            f"Tuesday to Saturday). Both share the Massive rate limit, so run the Blurb run after "
            f":{REFRESH_MINUTES} past the hour, or pass --force if the refresh has finished.{RESET}",
            file=sys.stderr,
        )
        sys.exit(1)
    if not ANTHROPIC_API_KEY:
        raise SystemExit("ANTHROPIC_API_KEY is missing; add it to backend/.env")

    conn = connect()
    init_schema(conn)
    rated = one(conn.execute("SELECT MAX(date) FROM rs_ratings"))[0]
    if rated is None:
        raise SystemExit("No RS Ratings yet; run the ETL first")
    today = date.today()
    behind = trading_days_behind(rated, today)
    if behind > STALE_TRADING_DAYS:
        print(f"{RED}Warning: the rated date {rated} is {behind} trading days old. Is the Daily refresh failing?{RESET}")

    leaders = load_leaders(conn, rated)
    if args.ticker:
        leaders = [l for l in leaders if l["ticker"] == args.ticker.upper()]
        if not leaders:
            raise SystemExit(f"{args.ticker.upper()} isn't a Leader on {rated}")
    leaders = leaders[: args.limit]

    skipped = run(conn, MassiveClient(), anthropic.Anthropic(api_key=ANTHROPIC_API_KEY), rated, today, leaders)
    print(f"\nBlurbs: {len(leaders) - len(skipped)} written for {rated}, {len(skipped)} skipped")
    if skipped:
        print(f"Skipped: {', '.join(skipped)}")
    if too_many_failures(skipped):
        sys.exit(1)


if __name__ == "__main__":
    main()
