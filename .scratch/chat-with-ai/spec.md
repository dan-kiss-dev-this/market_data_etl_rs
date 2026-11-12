# ChatWithAI: chat with the AI Researcher about a Leader

Status: ready-for-agent

## Problem Statement
The AI Researcher panel shows a Leader's weekly Blurb, but its chat input is disabled, so a trader can't ask follow-up questions such as "how does this compare to its rivals?" or "what would break the thesis?". The site has no logins, and every AI call costs money, so chat must have hard limits per visitor and for the whole site.

## Solution
A **ChatWithAI** module, made up of `backend/app/chat_with_ai.py` and `frontend/src/components/ChatWithAI.tsx`, adds a streamed chat to the panel for Leaders. Claude Haiku 5.5 answers from the Leader's stored Blurb, RS data, company description and Market direction. It doesn't use web search and makes no Massive call per message. Each anonymous visitor gets 5 messages per UTC day of up to 250 characters each, and the whole site gets 100 messages per day. The visitor key is the only part tied to anonymous visitors, so Supabase Auth can replace it later.

## Cost
- One message carries about 4–6K input tokens (instructions, Blurb, RS data, description and history) and at most 1,024 output tokens. At $0.10 / $0.50 per MTok that comes to about **$0.001 a message**.
- The site-wide cap of 100 a day limits spending to about **$0.11/day, about $3.30/month**.
- The system prompt is cached (top-level `cache_control`), so later turns in a conversation cost even less.
- As a last backstop, the owner sets a monthly spend limit in the Anthropic Console.

## User Stories
1. As a trader, I want to ask the AI Researcher follow-up questions about a Leader, so that I can dig into its Catalyst, rivals and risks.
2. As a trader, I want replies to stream in as they're written, so that the chat feels responsive.
3. As a trader, I want to see how many of my 5 messages are left today, so that I can use them well.
4. As a trader, I want an alert saying how many characters I'm over when my message is longer than 250 characters, with Send disabled, so that I know why I can't send it.
5. As a trader, I want a clear "Chat only works for Leaders, the top 50 companies by RS rating." on companies without a current Blurb.
6. As a trader, I want a clear message when I've used my 5 messages, or when the site's daily limit is reached.
7. As the owner, I want a hard site-wide daily cap, so that abuse can never cost more than about $0.11 a day.
8. As the owner, I want the limits in one module, so that I can require Supabase Auth logins later without rewriting the chat.

## Implementation Decisions
- **Model:** `claude-haiku-5-5` at low effort, with `max_tokens` 1,024 and streaming
- **Config** (`config.py`): `CHAT_MODEL`, `CHAT_VISITOR_DAILY = 5`, `CHAT_SITE_DAILY = 100`, `CHAT_MAX_CHARS = 250`, `CHAT_MAX_TOKENS = 1024`
- **Chat allowance:** the messages a visitor has left today. It's counted in `chat_usage (day, visitor, messages)`, where the row with visitor `'*'` holds the site total. `take_message` takes a `pg_advisory_xact_lock`, reads both counts, calls the pure function `decide(visitor_used, site_used)`, and if allowed adds 1 to both. `refund` subtracts it again when the Anthropic call fails before any text arrives.
- **Visitor key** (`visitor_key(request)`, the seam for Supabase Auth): `sha256(f"{day}:{ip}")`, with the IP taken from the first `X-Forwarded-For` entry (set by Render's proxy), falling back to `request.client.host`. Only the hash is stored. Visitors behind a shared IP share a limit. Someone who switches IPs can get past their own limit, but not the site cap.
- **Conversation state:** stateless. The client sends the whole conversation each time. The server checks it: roles alternate and start and end with `user`, there are at most 5 user turns, user messages are 1–250 chars, and assistant messages are at most 6,000 chars. Assistant messages come from the client and can't be trusted, so these caps also limit cost.
- **Context:** built from stored data only, using the existing helpers:
  - a new `current_blurb(conn, ticker, today)` extracted from `rs_blurb`
  - `load_leaders(conn, blurb_date)`, filtered to the ticker
  - `company_profiles.description`
  - `describe_market`

  A frozen block of instructions comes first so it can be cached: the site thesis, plain answers in a few sentences, no buy or sell advice, and saying so when the context doesn't cover a question.
- **Endpoints:**
  - `GET /api/chat/allowance` returns `{remaining, limit}`
  - `POST /api/rs/{ticker}/chat` streams `text/plain` and sends the allowance in an `X-Chat-Remaining` header. Errors come back before streaming starts:
    - 503: no `ANTHROPIC_API_KEY`, or no `chat_usage` table yet
    - 404: no current Blurb
    - 422: invalid conversation
    - 429 with `{reason: "visitor" | "site"}`
- **Refusals:** on `stop_reason == "refusal"` the reply is a short fixed line, and on `max_tokens` it ends with "…".
- **Frontend:** `ChatWithAI` replaces the disabled input in `AiResearcher`. Replies go in a `role="log"` list, kept apart from the panel's `role="status"` region so screen readers don't re-read it while text streams. The conversation resets when the ticker changes.

## Testing Decisions
- Backend, using the fake-connection and monkeypatch style of `test_blurbs.py`:
  - `decide` at both limits
  - request validation
  - `visitor_key` with and without `X-Forwarded-For`
  - the endpoint through `TestClient`: 404, 429, a streamed reply from a fake Anthropic client, and a refund on failure
- Frontend, using the style of `AiResearcher.test.tsx`:
  - the over-limit alert and the disabled Send button
  - non-Leaders disabled
  - a streamed reply
  - the 429 messages
  - the remaining count

## Out of Scope
- Logins (Supabase Auth). The visitor key is ready for it.
- Chat for companies that aren't Leaders
- Web search, or fetching live news per message
- Storing conversations on the server
