# 03: Deploy chat with a spend backstop

**What to build:** The production settings that turn chat on, and a hard spending backstop. See `../spec.md`.

**Blocked by:** 01, 02

**Status:** ready-for-human

- [ ] `render.yaml`: add `ANTHROPIC_API_KEY` with `sync: false` (done in the blueprint), then enter the key in the Render dashboard
- [x] `backend/.env.example`: note that the key also powers chat
- [ ] Set a monthly spend limit in the Anthropic Console (for example $10)
- [ ] Make sure `chat_usage` exists in Supabase (the next Daily refresh creates it, or run `uv run python -m app.etl` once)
- [ ] Production check: a Leader's reply streams, the counter goes down, the 6th message is blocked, a non-Leader shows the disabled input
- [ ] Check one response's `usage` to confirm about $0.001 a message and that `cache_read_input_tokens` is non-zero on the second turn
