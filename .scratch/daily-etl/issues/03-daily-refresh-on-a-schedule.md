# 03: Daily refresh runs overnight on a schedule

**What to build:** A scheduled GitHub Actions workflow runs the existing ETL unchanged against Supabase. Each morning the site shows the previous trading day's ratings with nobody touching it.
- **Schedule:** 07:00 UTC and 13:00 UTC, Tuesday to Saturday. The second run is the same-day retry if Massive publishes late. A comment in the workflow explains why it runs overnight: the free tier only serves a trading day after it ends, and the ETL fetches up to yesterday in UTC.
- **No manual trigger.** The workflow is schedule-only.
- **Safeguards:** one concurrency group, so runs never overlap and an in-progress run is never cancelled; a 30-minute timeout; read-only repository permissions; the two secrets passed as environment variables.
- **Install:** uv with a lockfile-keyed cache, production dependencies only, frozen lockfile.
- **Docs:**
  - A README Deployment section: the Render web service (`DATABASE_URL` set in the dashboard), the daily refresh schedule and why, the two secrets, GitHub's failure email, and the 60-day auto-disable with how to turn it back on.
  - Correct the README's "rerun it after the market closes" line: a new trading day is available after midnight ET.
  - Create `docs/todo-ideas.md` with the idea of a manual "Run workflow" button for on-demand refreshes.

See the spec: `.scratch/daily-etl/spec.md`.

**Blocked by:** 02 (Add the daily refresh secrets to GitHub)

**Status:** ready-for-agent

- [x] The workflow has only the two crons, with no `workflow_dispatch` trigger
- [x] actionlint reports no problems with the workflow
- [x] The workflow's ETL command, run locally against Supabase, succeeds and prints the Summary line
- [ ] After pushing (with the owner's OK), the first scheduled run succeeds and its log shows "Summary: … latest rating <previous trading day>"
- [ ] `/api/rs/status` on the Render site shows `rated_date` equal to the previous trading day
- [x] The README has the Deployment section and the corrected availability line
- [x] `docs/todo-ideas.md` records the manual-button idea
