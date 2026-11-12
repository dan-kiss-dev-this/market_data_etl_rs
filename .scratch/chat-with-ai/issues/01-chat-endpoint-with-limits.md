# 01: Chat endpoint with daily limits

**What to build:** `backend/app/chat_with_ai.py` and the two endpoints, `GET /api/chat/allowance` and `POST /api/rs/{ticker}/chat` (streamed). See `../spec.md`.

**Blocked by:** none

**Status:** ready-for-agent

- [x] Config: `CHAT_MODEL = "claude-haiku-5-5"`, `CHAT_VISITOR_DAILY = 5`, `CHAT_SITE_DAILY = 100`, `CHAT_MAX_CHARS = 250`, `CHAT_MAX_TOKENS = 1024`
- [x] Schema: `chat_usage (day, visitor, messages)` added to `SCHEMA`
- [x] `visitor_key(request)` hashes the day and the client IP (first `X-Forwarded-For` entry, else `request.client.host`)
- [x] `decide`, `take_message` (advisory lock, visitor and site `'*'` rows) and `refund`
- [x] Pydantic validation: alternating roles that start and end with `user`, at most 5 user turns, user messages 1–250 chars, assistant messages at most 6,000 chars
- [x] `current_blurb(conn, ticker, today)` extracted from `rs_blurb` and used by both endpoints
- [x] Context from the Blurb, `load_leaders` (filtered to the ticker), `company_profiles` and `describe_market`. No Massive call
- [x] Haiku 5.5 streamed at low effort with top-level `cache_control`. Refusal and `max_tokens` handled
- [x] Error codes: 503 (no key or no table), 404 (no current Blurb), 422, 429 `{reason}`. `X-Chat-Remaining` header on success
- [x] `backend/tests/test_chat_with_ai.py` covers the limits, validation, the visitor key, and the endpoint (404, 429, streaming, refund)
- [x] `uv run pytest` passes

## Comments

- The visitor key uses the first `X-Forwarded-For` entry. A visitor can fake it to get past their own 5/day, the same as switching networks, but not the site cap of 100/day. If abuse shows up, move to Supabase Auth by changing `visitor_key`.
- `MAX_REPLY_CHARS` is 6,000 rather than 4,000: a 1,024-token reply can run past 4,000 characters and would then be rejected when the browser sends it back as history.
- `/api/chat/allowance` also returns `reason`, so the panel can tell "you've used yours" apart from "the site is busy".
- A failed Anthropic call before any text returns 502 and gives the message back.
