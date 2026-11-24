# 04: Turn on Row-Level Security for every public table

Status: ready-for-agent

**What to build:** Supabase emailed a critical `rls_disabled_in_public` alert. Supabase puts every `public` table on its REST API (PostgREST), and the anon key for that API is meant to be public. Without RLS, anyone who has the key can read, change or delete rows. The site never uses that API: the browser only calls `/api/...` on Render, and the backend, the Daily refresh and `pull_prod` connect to Postgres directly as `postgres`, the role that owns the tables. Owners bypass RLS unless it is FORCEd. So RLS with no policies shuts the REST API (no rows, no writes) and changes nothing for the app.

Add `uv run --env-file .env.production python -m app.enable_rls`, which the owner runs by hand, for example after adding a table. It enables RLS on every `public` table that doesn't have it yet, including tables the code doesn't create, in one transaction, and prints what it changed. An `ALTER TABLE ... ADD COLUMN` keeps RLS on, so only new tables need it.

**Blocked by:** none

- [x] Tests first (`tests/test_enable_rls.py`): which tables are missing RLS, and the statements enable it without FORCE. Seen failing.
- [x] `app/enable_rls.py`
- [x] README note under "Changing the schema"
- [x] Run locally twice: the first run lists tables, the second says already on
- [ ] Run against Supabase; Advisors → Security is clean; the Daily refresh still succeeds

## Comments

- Verified on local Postgres, 2026-11-24. The first run turned on RLS for all 12 tables, the second printed "RLS already on for all 12 tables". `/api/rs/status` and `/api/rs/leaders` (50 rows) still served data. pytest 88/88, ruff clean.
- Still to do (owner, since it needs `.env.production`): run it against Supabase, re-run Advisors → Security, and check the next Daily refresh.
