import pytest

from app import chat_with_ai
from app.blurbs import current_blurb
from app.chat_with_ai import Message
from evals.high_close import CASES, Case, check


def context_for(conn, ticker: str) -> str:
    """The real chat context when the ticker has a current Blurb, else just its name."""
    blurb = current_blurb(conn, ticker)
    return chat_with_ai.leader_context(conn, blurb) if blurb else f"Company: {ticker}"


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_high_close(case: Case, conn, ai, monkeypatch):
    calls: list[dict] = []
    real = chat_with_ai.run_tool

    def recording(name: str, tool_input: dict) -> dict:
        calls.append({"name": name, "input": tool_input})
        return real(name, tool_input)

    monkeypatch.setattr(chat_with_ai, "run_tool", recording)
    text = "".join(
        chat_with_ai.reply(ai, context_for(conn, case.ticker), [Message(role="user", content=case.question)])
    )
    row = chat_with_ai.high_close(conn, case.asks_about or case.ticker)
    failure = check(case, text, calls, row)
    assert failure is None, f"{failure}\nreply: {text!r}"
