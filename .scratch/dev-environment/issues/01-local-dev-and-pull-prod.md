# 01: Local Postgres for dev, Supabase only on request

**What to build:** Make local Postgres the default database for every local command. Supabase (production) is used only with `--env-file .env.production`. Add `uv run python -m app.pull_prod`, which copies only the data local is missing from Supabase.

**Blocked by:** none

**Status:** ready-for-agent

- [x] `DATABASE_URL` moved from `backend/.env` to a gitignored `backend/.env.production`
- [x] `.gitignore` covers `.env.*` except `.env.example`
- [x] `app.pull_prod`: read-only on Supabase, refuses a non-local target, runs `init_schema`
- [x] Small tables replaced, `daily_bars` copied for new dates plus full re-copies of split/renamed tickers, `rs_ratings` recomputed with `compute_rs`, `chat_usage` skipped
- [x] Tests for the localhost guard and the re-copy ticker choice
- [x] README and ADR 0001 updated
- [x] A second run copies 0 new rows; local matches Supabase on `daily_bars`, `rs_ratings` and `blurbs`

## Comments

- The ticker histories to re-copy are found by comparing each ticker's bar count and close sum, up to dev's last date, between the two databases. That replaces the plan's "new `splits_applied`/`history_checked` row" check: it catches any rewrite, including a new S&P constituent's backfilled history.
- First run: +2,520 `daily_bars` rows after 2026-11-04, 0 tickers re-copied, ratings through 2026-11-11, 50 Blurbs; about 6 s. Dev matched production on bar and rating counts and on the sum of every RS rating. A second run copied 0 rows.
- `backend/.env` still has an unused `SUPABASE_DB_URL` line; nothing reads it.
