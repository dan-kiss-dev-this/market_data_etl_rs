from contextlib import contextmanager, nullcontext
from datetime import date

import anthropic
import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import chat_with_ai, main
from app.chat_with_ai import Allowance, Conversation, LimitReached

DAY = date(2026, 11, 12)
BLURB = {
    "ticker": "NVDA",
    "date": "2026-11-10",
    "blurb": {
        "what_they_sell": "GPUs.", "catalyst": "Earnings beat.", "category_position": "Leader.",
        "momentum": "RS 97.", "risks": "Export limits.",
    },
    "headlines": [{"date": "2026-11-05", "title": "Nvidia beats", "publisher": "Reuters", "url": "u"}],
    "market": None,
}  # fmt: skip
LEADER = {
    "ticker": "NVDA", "name": "Nvidia", "sector": "Information Technology", "rs_rating": 97,
    "rs_score": 180.0, "ret_3m": 0.25, "ret_12m": 0.8, "rs_new_high": True,
    "sector_rank": 2, "sector_size": 68, "rating_change_1w": 3,
}  # fmt: skip


def conversation(*contents: str) -> list[dict]:
    return [{"role": "user" if i % 2 == 0 else "assistant", "content": c} for i, c in enumerate(contents)]


def test_visitor_limit_comes_before_the_site_limit():
    assert chat_with_ai.decide(0, 0) == Allowance(5)
    assert chat_with_ai.decide(4, 50) == Allowance(1)
    assert chat_with_ai.decide(5, 100) == Allowance(0, "visitor")
    assert chat_with_ai.decide(2, 100) == Allowance(0, "site")
    assert chat_with_ai.decide(1, 98) == Allowance(2)  # only 2 left on the site


def test_conversation_must_alternate_and_end_with_the_user():
    Conversation(messages=conversation("Hi", "Hello", "Rivals?"))
    for bad in ([], conversation("Hi", "Hello"), [{"role": "assistant", "content": "Hi"}],
                [{"role": "user", "content": "a"}, {"role": "user", "content": "b"}]):  # fmt: skip
        with pytest.raises(ValidationError):
            Conversation(messages=bad)


def test_user_messages_are_capped_at_250_characters_and_5_per_conversation():
    Conversation(messages=conversation("x" * 250))
    with pytest.raises(ValidationError):
        Conversation(messages=conversation("x" * 251))
    with pytest.raises(ValidationError):
        Conversation(messages=conversation("   "))
    with pytest.raises(ValidationError):
        Conversation(messages=conversation("q", "a" * 6001, "q"))
    with pytest.raises(ValidationError):
        Conversation(messages=conversation(*["q", "a"] * 5, "q"))


class FakeRequest:
    def __init__(self, forwarded: str | None = None, host: str = "10.0.0.1"):
        self.headers = {"x-forwarded-for": forwarded} if forwarded else {}
        self.client = type("Client", (), {"host": host})()


def test_visitor_key_uses_the_first_forwarded_ip_and_changes_each_day():
    proxied = chat_with_ai.visitor_key(FakeRequest("1.2.3.4, 10.0.0.9"), DAY)
    assert proxied == chat_with_ai.visitor_key(FakeRequest("1.2.3.4"), DAY)
    assert proxied != chat_with_ai.visitor_key(FakeRequest(), DAY)
    assert proxied != chat_with_ai.visitor_key(FakeRequest("1.2.3.4"), date(2026, 11, 13))
    assert "1.2.3.4" not in proxied


def test_context_has_the_blurb_rs_data_and_cited_headlines():
    context = chat_with_ai.build_context(BLURB, LEADER, "Makes GPUs.")
    assert "Company: Nvidia (NVDA), sector: Information Technology" in context
    assert "- Catalyst: Earnings beat." in context
    assert "RS rating 97 (1-week change: +3), rank 2 of 68" in context
    assert "- 2026-11-05 · Reuters · Nvidia beats" in context
    assert "Market direction: Not available." in context


class FakeStream:
    def __init__(self, texts: list[str], stop_reason: str = "end_turn", fail: bool = False):
        self.texts, self.stop_reason, self.fail = texts, stop_reason, fail

    def __enter__(self):
        if self.fail:
            raise anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com"))
        return self

    def __exit__(self, *exc):
        return False

    @property
    def text_stream(self):
        yield from self.texts

    def get_final_message(self):
        return type("Message", (), {"stop_reason": self.stop_reason})()


class FakeAnthropic:
    def __init__(self, stream: FakeStream):
        self.messages = self
        self.stream_ = stream
        self.calls: list[dict] = []

    def stream(self, **kwargs):
        self.calls.append(kwargs)
        return self.stream_


def test_reply_streams_text_and_handles_refusals():
    ai = FakeAnthropic(FakeStream(["Nvidia ", "leads."]))
    assert list(chat_with_ai.reply(ai, "ctx", Conversation(messages=conversation("Rivals?")).messages)) == ["Nvidia ", "leads."]
    assert ai.calls[0]["model"] == "claude-haiku-5-5"
    assert ai.calls[0]["messages"] == [{"role": "user", "content": "Rivals?"}]
    assert ai.calls[0]["system"][1]["text"] == "ctx"

    refused = FakeAnthropic(FakeStream([], stop_reason="refusal"))
    assert list(chat_with_ai.reply(refused, "ctx", [])) == [chat_with_ai.REFUSED]


@pytest.fixture
def api(monkeypatch):
    """The chat endpoint with the database and Anthropic replaced; returns what the fakes record."""
    calls = {"refunds": 0, "taken": 0}

    class Pool:
        @contextmanager
        def connection(self):
            yield None

    def take(conn, visitor, day):
        calls["taken"] += 1
        return Allowance(4)

    def refund(conn, visitor, day):
        calls["refunds"] += 1

    monkeypatch.setattr(main, "ANTHROPIC_API_KEY", "test")
    monkeypatch.setattr(main, "pool", lambda: Pool())
    monkeypatch.setattr(main, "current_blurb", lambda conn, ticker, today: BLURB if ticker == "NVDA" else None)
    monkeypatch.setattr(chat_with_ai, "leader_context", lambda conn, blurb: "ctx")
    monkeypatch.setattr(chat_with_ai, "take_message", take)
    monkeypatch.setattr(chat_with_ai, "refund", refund)
    monkeypatch.setattr(chat_with_ai, "ai_client", lambda: FakeAnthropic(FakeStream(["Nvidia ", "leads."])))
    calls["client"] = TestClient(main.app)
    return calls


def test_chat_streams_the_reply_with_the_remaining_count(api):
    res = api["client"].post("/api/rs/nvda/chat", json={"messages": conversation("Rivals?")})
    assert res.status_code == 200
    assert res.text == "Nvidia leads."
    assert res.headers["x-chat-remaining"] == "4"


def test_chat_only_works_for_leaders(api):
    res = api["client"].post("/api/rs/MRNA/chat", json={"messages": conversation("Rivals?")})
    assert res.status_code == 404
    assert api["taken"] == 0


def test_chat_over_the_limit_is_429_with_the_reason(api, monkeypatch):
    def full(conn, visitor, day):
        raise LimitReached("site")

    monkeypatch.setattr(chat_with_ai, "take_message", full)
    res = api["client"].post("/api/rs/NVDA/chat", json={"messages": conversation("Rivals?")})
    assert res.status_code == 429
    assert res.json() == {"detail": {"reason": "site"}}


def test_too_long_message_is_rejected_before_counting(api):
    res = api["client"].post("/api/rs/NVDA/chat", json={"messages": conversation("x" * 251)})
    assert res.status_code == 422
    assert api["taken"] == 0


def test_failed_ai_call_gives_the_message_back(api, monkeypatch):
    monkeypatch.setattr(chat_with_ai, "ai_client", lambda: FakeAnthropic(FakeStream([], fail=True)))
    res = api["client"].post("/api/rs/NVDA/chat", json={"messages": conversation("Rivals?")})
    assert res.status_code == 502
    assert api["refunds"] == 1


def test_chat_without_an_api_key_is_unavailable(api, monkeypatch):
    monkeypatch.setattr(main, "ANTHROPIC_API_KEY", "")
    assert api["client"].post("/api/rs/NVDA/chat", json={"messages": conversation("Hi")}).status_code == 503
    assert api["client"].get("/api/chat/allowance").status_code == 503


def test_take_message_refuses_once_the_visitor_is_out(monkeypatch):
    monkeypatch.setattr(chat_with_ai, "usage", lambda conn, visitor, day: (5, 10))
    conn = type("Conn", (), {"transaction": lambda self: nullcontext(), "execute": lambda self, *a: None})()
    with pytest.raises(LimitReached) as e:
        chat_with_ai.take_message(conn, "v", "2026-11-12")
    assert e.value.reason == "visitor"
