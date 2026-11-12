# 04: Daily refresh reaches Supabase over IPv4

**What to fix:** Both scheduled Daily refresh runs on 2026-11-12 (15:54 and 20:38 UTC, run IDs 43252863346 and 43302389709) failed in `connect()` (`backend/app/db.py`) with `psycopg.OperationalError: connection to server at "2600:1f16:…:63a2", port 5432 failed: Network is unreachable`.
- **Cause:** the `DATABASE_URL` secret uses Supabase's direct-connection host (`db.<ref>.supabase.co`), which only has an IPv6 address. GitHub-hosted runners have no IPv6. The ETL works locally only because the machine running it has IPv6.
- **Fix:** set the secret to the Supabase **Session pooler** URL (`postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres`), which is IPv4. The owner does this, since the secret holds the password: `gh secret set DATABASE_URL`. No code change is needed: `CONNECT_KWARGS` already sets `prepare_threshold=None`, so the transaction pooler (port 6543) would work too.
- **Consistency:** check that Render's `DATABASE_URL` and the prod URL that `pull_prod` uses also point at the pooler.

**Blocked by:** none

**Status:** ready-for-human

- [x] `DATABASE_URL` secret updated to the pooler URL (2026-11-12 23:06 UTC, from `backend/.env.production`)
- [ ] The next scheduled run (07:00 UTC) succeeds and its log shows the Summary line
- [ ] Optional: bump `astral-sh/setup-uv@v6` to a version that runs on Node 24 (clears the deprecation warning, which is not the cause of the failure)
