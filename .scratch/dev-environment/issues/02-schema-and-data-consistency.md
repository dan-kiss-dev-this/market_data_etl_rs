# 02: Schema changes reach Supabase only through a tested deploy; pull_prod copies every table

**What to build:** Keep the schema and data consistent between Supabase (production) and local Postgres (dev).
- **Schema:** one source of truth in `app/db.py`: `SCHEMA` for new tables, an append-only `MIGRATIONS` list for changes to existing tables. Supabase's schema changes only when the API starts on Render, and Render deploys only after the Tests workflow passes. The ETL and the Blurb run check the schema against Supabase; they never change it.
- **Data:** data flows one way, production → local. `pull_prod` copies every table except an explicit skip list, and it reports drift between the two schemas instead of failing on it.

**Blocked by:** none

**Status:** ready-for-agent

- [x] `schema_migrations` table, `MIGRATIONS` list, `init_schema` applies pending ones under an advisory lock in one transaction
- [x] API startup (`lifespan`) runs `init_schema`
- [x] `ensure_schema`: applies on local Postgres, only checks (and fails clearly) anywhere else; `etl` and `blurbs` use it
- [x] `render.yaml`: `autoDeployTrigger: checksPass` (the Blueprint has Auto Sync on, checked 2026-11-13)
- [x] `pull_prod`: `SKIPPED` replaces `SMALL_TABLES`, copies only shared columns, skips tables production lacks, prints differences
- [x] Tests: pending versions, schema gaps, migrations are additive, which tables and columns `pull_prod` copies
- [x] README (changing the schema, backups, deploy after tests) and ADR 0001 updated

## Comments

- Hand-rolled migrations rather than Alembic: the backend is raw SQL through psycopg with no SQLAlchemy, and there are about 10 tables.
- Production must not be wiped. Migrations are additive only (a test enforces it), and they run in one transaction. `pull_prod` stays read-only on Supabase. A new column on `daily_bars` doesn't trigger any re-fetch from Massive.
- Verified on local Postgres, 2026-11-13. A temporary migration (`companies.tmp_check`) was applied on the first API start and not re-applied on the second. `pull_prod` then reported the column and `schema_migrations` as drift and still copied the same 7 tables, plus 504 new bars through 2026-11-12. After cleanup, a second pull copied 0 rows.
- `ensure_schema` against Supabase, in a read-only session, refused with "behind this code (table schema_migrations)", as intended until the first deploy creates it. The next Daily refresh is Tuesday 07:00 UTC, so the deploy will be done long before then.
- Not verified yet (needs the push): the Render deploy waits for the Tests workflow, and Supabase gets `schema_migrations` at startup.
