"""Eval for the get_high_close_past_2_years tool: does the AI Researcher call it for all-time, past-year
and past-2-years high questions (and only then), and answer with the stored price, its date and the
2-year caveat?

Runs live against real Haiku and DATABASE_URL, so the expected prices are read from
high_close_past_2_years at run time. Run from backend/ by hand (not in CI; a run costs about 1¢):
    uv run python -m evals.high_close_eval
"""

import re
import sys
from dataclasses import dataclass
from datetime import date

from app import chat_with_ai
from app.blurbs import current_blurb
from app.chat_with_ai import Message
from app.db import connect

TOOL = "get_high_close_past_2_years"
CAVEAT = re.compile(r"\b(2|two)[- ]years?\b|\b24 months\b", re.IGNORECASE)


@dataclass(frozen=True)
class Case:
    name: str
    ticker: str  # the Leader whose chat the question is asked in
    question: str
    expect_tool: bool
    # The ticker the tool should be asked about, and whose stored row the answer should quote
    asks_about: str | None = None
    no_row: bool = False


CASES = [
    Case("all-time", "NVDA", "What is the all time high for NVDA?", True),
    Case("past-year", "NVDA", "What was its highest close in the past year?", True),
    Case("past-2-years", "AAPL", "Highest price in the last 2 years?", True),
    Case("other-ticker", "AAPL", "What's Tesla's (TSLA) all-time high close?", True, asks_about="TSLA"),
    Case("no-row", "NVDA", "What's the all-time high for Rivian (RIVN)?", True, asks_about="RIVN", no_row=True),
    Case("unrelated", "NVDA", "What are its risks?", False),
]


def date_forms(iso: str) -> list[str]:
    """The ways a reply might write a date: 2025-07-10, July 10, 2025, Jul 10, 2025, 10 July 2025."""
    d = date.fromisoformat(iso)
    month, short = d.strftime("%B"), d.strftime("%b")
    return [iso, f"{month} {d.day}, {d.year}", f"{short} {d.day}, {d.year}", f"{d.day} {month} {d.year}"]


def price_forms(close: float) -> list[str]:
    return [f"${close:,.2f}", f"${close:.2f}"]


def context_for(conn, ticker: str) -> str:
    """The real chat context when the ticker has a current Blurb, else just its name."""
    blurb = current_blurb(conn, ticker, date.today())
    return chat_with_ai.leader_context(conn, blurb) if blurb else f"Company: {ticker}"


def check(case: Case, text: str, calls: list[dict], row: dict | None) -> str | None:
    """Why the case failed, or None if it passed."""
    tool_calls = [c for c in calls if c["name"] == TOOL]
    if not case.expect_tool:
        return f"tool called {len(tool_calls)} times, expected none" if tool_calls else None
    if len(tool_calls) != 1:
        return f"tool called {len(tool_calls)} times, expected once"
    asked = tool_calls[0]["input"].get("ticker", "").upper()
    if asked != (case.asks_about or case.ticker):
        return f"tool asked about {asked!r}, expected {case.asks_about or case.ticker!r}"
    if case.no_row:
        return "quoted a price with no stored row" if re.search(r"\$\d", text) else None
    if row is None:
        return f"no stored row for {asked}; run the ETL first"
    if not any(p in text for p in price_forms(row["close"])):
        return f"price {price_forms(row['close'])[0]} missing"
    if not any(d in text for d in date_forms(row["date"])):
        return f"date {row['date']} missing"
    if not CAVEAT.search(text):
        return "doesn't say it's the high of the last 2 years"
    return None


def run(case: Case, conn, ai) -> str | None:
    calls: list[dict] = []
    real = chat_with_ai.run_tool

    def recording(name: str, tool_input: dict) -> dict:
        calls.append({"name": name, "input": tool_input})
        return real(name, tool_input)

    chat_with_ai.run_tool = recording
    try:
        text = "".join(chat_with_ai.reply(ai, context_for(conn, case.ticker), [Message(role="user", content=case.question)]))
    finally:
        chat_with_ai.run_tool = real
    row = chat_with_ai.high_close(conn, case.asks_about or case.ticker)
    failure = check(case, text, calls, row)
    if failure:
        print(f"    reply: {text!r}")
    return failure


def main() -> None:
    conn = connect()
    ai = chat_with_ai.ai_client()
    failed = 0
    for case in CASES:
        failure = run(case, conn, ai)
        print(f"{'FAIL' if failure else 'PASS'} {case.name}" + (f": {failure}" if failure else ""))
        failed += failure is not None
    print(f"\n{len(CASES) - failed}/{len(CASES)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
