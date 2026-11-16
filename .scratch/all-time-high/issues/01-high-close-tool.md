# 01: The chat answers "all-time high" questions from a stored 2-year high close

**What to build:** A `high_close_past_2_years (ticker, date, close)` table holding each ticker's highest close in `daily_bars`, rebuilt by every Daily refresh after `compute_rs`. The chat gets its first tool, `get_high_close_past_2_years`, which it calls when a trader asks for the all-time high, or the highest close in the past year or past 2 years. The reply gives the price and the date, and says it's the highest close in the last 2 years because that's all the history we store.

**Blocked by:** None

**Status:** ready-for-agent

- [x] Eval `backend/evals/high_close_eval.py` written first and seen failing (live Haiku + `DATABASE_URL`, run by hand)
- [x] Tests first: the schema has the table; the 2-year high picks the highest close (latest date on a tie); the ETL rebuilds it after `compute_rs`; `reply` runs the tool and sends back its result
- [x] `high_close_past_2_years` in `db.SCHEMA`; `app/high_close.py` rebuilds it; `etl.main` and `pull_prod` call it
- [x] `chat_with_ai`: `HIGH_CLOSE_TOOL`, `high_close` lookup, a tool loop in `reply` (at most 3 rounds), and a system prompt line about the 2-year caveat
- [x] GLOSSARY, README and the chat-with-ai spec updated
- [x] `uv run pytest` passes and the eval passes

## Comments

- `daily_bars` holds about 725 days (`etl.DEFAULT_DAYS`), so "all-time" and "past year" questions both get the 2-year high with that caveat, as the owner asked.
- The rebuild is full each run, not incremental, because split adjustments and rename rebuilds rewrite past closes.
- Verified on local Postgres, 2026-11-16: `app.etl --rs-only` stored 505 tickers, and all of them match `max(close)` from `daily_bars` (for example, NVDA $239.24 on 2026-10-06). `evals.high_close_eval` passed 6/6 on two runs.
- Deploy to Render before the next Daily refresh. On Supabase, `ensure_schema` exits if the new table is missing.
