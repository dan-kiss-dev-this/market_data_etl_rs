"""ChatWithAI: answers follow-up questions about a Leader in the AI Researcher panel, from its
stored Blurb, RS data, description and the Market direction, within daily message limits.

Visitors are anonymous for now. visitor_key is the one place to change to key the limits on a
logged-in (Supabase Auth) user instead.
"""

import hashlib
import json
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from functools import cache
from typing import Literal

import anthropic
import psycopg
from fastapi import Request
from pydantic import BaseModel, model_validator

from app.blurbs import describe_market, load_leaders, pct
from app.config import (
    ANTHROPIC_API_KEY,
    CHAT_MAX_CHARS,
    CHAT_MAX_TOKENS,
    CHAT_MODEL,
    CHAT_SITE_DAILY,
    CHAT_VISITOR_DAILY,
)
from app.db import Row, pool

# The chat_usage row that counts the whole site's messages
SITE = "*"
# Replies come back from the browser with each message, so cap them too (1,024 tokens is about 4,500 chars)
MAX_REPLY_CHARS = 6000

SYSTEM_PROMPT = """You are the AI Researcher on a momentum trading site. The site's thesis is that \
the best momentum stocks combine high relative strength with innovative new products and leadership of \
their category. A trader is asking follow-up questions about one Leader (one of the 50 highest RS-rated \
S&P 500 companies). Below are its Blurb, RS data, description, the headlines the Blurb's Catalyst cites \
and the Market direction.

Answer in a few plain sentences. You may use general knowledge about the company, its products and \
its rivals, but take recent events only from the context: if the context doesn't cover something \
recent, say so instead of guessing. Be concrete. No hype, and never advise buying or selling.

For the all-time high, or the highest close or price in the past year or past 2 years, of this or any \
other ticker, use the get_high_close_past_2_years tool. Give the price and its date, and say it's the \
highest close in the last 2 years, as that's all the price history the site has. If it has no data, say \
so and don't give a price."""

HIGH_CLOSE_TOOL = {
    "name": "get_high_close_past_2_years",
    "description": "The highest daily close of an S&P 500 ticker in the last 2 years, with its date. Use it "
    "when the user asks for the all-time high, or the highest close or price in the past year or past 2 years. "
    "The site only has the last 2 years of daily closes, so this is the highest it knows of.",
    "input_schema": {
        "type": "object",
        "properties": {"ticker": {"type": "string", "description": "The ticker symbol, such as NVDA"}},
        "required": ["ticker"],
    },
}
# Model calls per reply, so a model that keeps asking for tools can't run up the bill
MAX_ROUNDS = 3

REFUSED = "I can't help with that one. Try asking about the company, its Catalyst, its rivals or its risks."

FIELDS = [
    ("what_they_sell", "What they sell"),
    ("catalyst", "Catalyst"),
    ("category_position", "Category position"),
    ("momentum", "Momentum"),
    ("risks", "Risks"),
]


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class Conversation(BaseModel):
    """The whole conversation so far, sent by the browser with each new message."""

    messages: list[Message]

    @model_validator(mode="after")
    def check(self):
        roles = [m.role for m in self.messages]
        if not roles or roles[-1] != "user" or roles != ["user", "assistant"] * (len(roles) // 2) + ["user"]:
            raise ValueError("messages must alternate user and assistant, starting and ending with user")
        if roles.count("user") > CHAT_VISITOR_DAILY:
            raise ValueError(f"at most {CHAT_VISITOR_DAILY} messages per conversation")
        for m in self.messages:
            limit = CHAT_MAX_CHARS if m.role == "user" else MAX_REPLY_CHARS
            if not m.content.strip() or len(m.content) > limit:
                raise ValueError(f"{m.role} messages must be 1 to {limit} characters")
        return self


@dataclass(frozen=True)
class Allowance:
    remaining: int
    # Why none are left: the visitor used theirs, or the site used its daily cap
    reason: Literal["visitor", "site"] | None = None


class LimitReached(Exception):
    def __init__(self, reason: Literal["visitor", "site"]):
        super().__init__(reason)
        self.reason = reason


def client_ip(request: Request) -> str:
    # Render's proxy puts the visitor's IP in X-Forwarded-For. A visitor can prepend a fake one to
    # get past their own limit, like switching networks; the site cap still holds
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def visitor_key(request: Request, day: date) -> str:
    """Who the limits count against: a hash of the day and the visitor's IP, so no IP is stored."""
    return hashlib.sha256(f"{day.isoformat()}:{client_ip(request)}".encode()).hexdigest()


def decide(visitor_used: int, site_used: int) -> Allowance:
    if visitor_used >= CHAT_VISITOR_DAILY:
        return Allowance(0, "visitor")
    if site_used >= CHAT_SITE_DAILY:
        return Allowance(0, "site")
    return Allowance(min(CHAT_VISITOR_DAILY - visitor_used, CHAT_SITE_DAILY - site_used))


def usage(conn: psycopg.Connection[Row], visitor: str, day: str) -> tuple[int, int]:
    rows = conn.execute(
        "SELECT visitor, messages FROM chat_usage WHERE day = %s AND visitor IN (%s, %s)", (day, visitor, SITE)
    ).fetchall()
    counts = {r["visitor"]: r["messages"] for r in rows}
    return counts.get(visitor, 0), counts.get(SITE, 0)


def allowance(conn: psycopg.Connection[Row], visitor: str, day: str) -> Allowance:
    return decide(*usage(conn, visitor, day))


def add_messages(conn: psycopg.Connection[Row], visitor: str, day: str, n: int) -> None:
    for who in (visitor, SITE):
        conn.execute(
            """INSERT INTO chat_usage VALUES (%s, %s, %s)
               ON CONFLICT (day, visitor) DO UPDATE SET messages = chat_usage.messages + EXCLUDED.messages""",
            (day, who, n),
        )


def take_message(conn: psycopg.Connection[Row], visitor: str, day: str) -> Allowance:
    """Count one message against the visitor and the site; returns what's left after it."""
    with conn.transaction():
        # Serialises concurrent sends so two requests can't both take the last message
        conn.execute("SELECT pg_advisory_xact_lock(hashtext('chat_usage'))")
        visitor_used, site_used = usage(conn, visitor, day)
        before = decide(visitor_used, site_used)
        if before.reason:
            raise LimitReached(before.reason)
        add_messages(conn, visitor, day, 1)
    return decide(visitor_used + 1, site_used + 1)


def refund(conn: psycopg.Connection[Row], visitor: str, day: str) -> None:
    """Give a message back when the AI couldn't answer it."""
    with conn.transaction():
        add_messages(conn, visitor, day, -1)


def build_context(blurb: dict, leader: dict | None, description: str) -> str:
    fields = "\n".join(f"- {label}: {blurb['blurb'][key]}" for key, label in FIELDS)
    headlines = "\n".join(f"- {h['date']} · {h['publisher']} · {h['title']}" for h in blurb["headlines"])
    if leader is None:
        rs = "Not available."
    else:
        change = leader["rating_change_1w"]
        rs = (
            f"RS rating {leader['rs_rating']} (1-week change: {'n/a' if change is None else f'{change:+d}'}), "
            f"rank {leader['sector_rank']} of {leader['sector_size']} in its sector; "
            f"RS line at a new high: {'yes' if leader['rs_new_high'] else 'no'}; "
            f"3-month return {pct(leader['ret_3m'])}, 12-month return {pct(leader['ret_12m'])}"
        )
    name = f"{leader['name']} ({blurb['ticker']}), sector: {leader['sector']}" if leader else blurb["ticker"]
    return f"""Company: {name}
Description: {description or 'Not available.'}

Blurb as of {blurb['date']}:
{fields}

RS data as of {blurb['date']}: {rs}

Market direction: {describe_market(blurb['market'])}

Headlines the Catalyst cites:
{headlines or 'None.'}"""


def leader_context(conn: psycopg.Connection[Row], blurb: dict) -> str:
    """The context for one Leader, from the database only (no Massive calls per message)."""
    leader = next((l for l in load_leaders(conn, blurb["date"]) if l["ticker"] == blurb["ticker"]), None)
    profile = conn.execute("SELECT description FROM company_profiles WHERE ticker = %s", (blurb["ticker"],)).fetchone()
    return build_context(blurb, leader, profile["description"] if profile else "")


def high_close(conn: psycopg.Connection[Row], ticker: str) -> dict | None:
    """The ticker's 2-year high close, or None if it has no bars."""
    row = conn.execute(
        "SELECT ticker, date, close FROM high_close_past_2_years WHERE ticker = %s", (ticker.upper(),)
    ).fetchone()
    return {"ticker": row["ticker"], "date": row["date"], "close": row["close"]} if row else None


def run_tool(name: str, tool_input: dict) -> dict:
    """Answer one tool call. It opens its own connection, as the request's is closed while the reply streams."""
    if name != HIGH_CLOSE_TOOL["name"]:
        return {"error": f"unknown tool {name}"}
    ticker = str(tool_input.get("ticker", "")).upper()
    with pool().connection() as conn:
        return high_close(conn, ticker) or {"error": f"no data for {ticker}"}


@cache
def ai_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def reply(ai: anthropic.Anthropic, context: str, messages: list[Message]) -> Iterator[str]:
    """Stream the AI Researcher's answer to the last message, running any tools it asks for."""
    history: list = [m.model_dump() for m in messages]
    for _ in range(MAX_ROUNDS):
        with ai.messages.stream(
            model=CHAT_MODEL,
            max_tokens=CHAT_MAX_TOKENS,
            system=[{"type": "text", "text": SYSTEM_PROMPT}, {"type": "text", "text": context}],
            messages=history,
            tools=[HIGH_CLOSE_TOOL],
            output_config={"effort": "low"},
            # Caches the instructions, context and history, so each later turn reads them cheaply
            cache_control={"type": "ephemeral"},
        ) as stream:
            yield from stream.text_stream
            final = stream.get_final_message()
        stop_reason = final.stop_reason
        if stop_reason != "tool_use":
            break
        results = [
            {"type": "tool_result", "tool_use_id": b.id, "content": json.dumps(run_tool(b.name, b.input))}
            for b in final.content
            if b.type == "tool_use"
        ]
        history = [*history, {"role": "assistant", "content": final.content}, {"role": "user", "content": results}]
    if stop_reason == "refusal":
        yield REFUSED
    elif stop_reason in ("max_tokens", "tool_use"):
        yield "…"
