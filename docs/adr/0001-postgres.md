# 1. Store market data in Postgres instead of SQLite

Date: 2026-11-05
Status: Accepted

## Context
Every table (companies, daily_bars, rs_ratings and the ETL bookkeeping tables) lived in one SQLite file, `backend/data/market.db`. A file inside the repo can't be shared by a deployed API and a separately scheduled ETL. We also want to be able to host the data on Supabase.

## Decision
- Use Postgres, reached through one connection string, `DATABASE_URL`. The default is the local Postgres.app database `postgresql://postgres@localhost:5432/market`; Supabase is a different URL (its session pooler).
- Talk to it with **psycopg 3** and plain SQL, not supabase-py. The queries are analytical (joins, window functions, bulk loads), and supabase-py goes through Supabase's REST API.
- Keep dates as `TEXT` ISO strings so ordering and the API's JSON stay exactly as they were. Floats are `DOUBLE PRECISION`; `rs_new_high` is `BOOLEAN`.
- Connections use `autocommit=True`, and writes are grouped with `conn.transaction()`. `prepare_threshold=None` keeps Supabase's transaction pooler working.
- A one-off script (`app.migrate_sqlite`) copied the existing data over. Both it and `market.db` were later removed; they remain in git history at commit `925b415`. Backups are now `pg_dump` files in `backend/data/backups/` (gitignored).

## Consequences
- Local development needs a running Postgres (Postgres.app) with a `market` database.
- Moving to Supabase is a data copy plus a `DATABASE_URL` change; no code changes.
- SQLite is no longer supported by the app.
