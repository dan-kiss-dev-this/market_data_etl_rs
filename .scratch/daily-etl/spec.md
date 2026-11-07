# Daily refresh via GitHub Actions

Status: ready-for-agent

## Problem Statement
The RS Ratings site is live on Render and reads from Supabase, but nothing refreshes the data. The rated date only moves forward when someone runs the ETL by hand on their laptop. If the owner forgets or is away, visitors see stale ratings with no warning. The owner wants it to update every trading day automatically.

An earlier draft of this spec scheduled the refresh at 22:00 UTC, "after the close". That doesn't work on Massive's free tier. The free tier won't serve a trading day until that day has ended; asking at 7:41 pm ET returned 403 "before end of day". The ETL also only fetches up to yesterday, by the runner's UTC date. So a run at the close would always be one trading day behind.

## Solution
A GitHub Actions workflow runs the daily refresh overnight. By US morning, the site shows the previous trading day's ratings. It needs no server, costs nothing (the repo is public), and needs no attention. A second run later the same morning retries automatically if Massive was late. If a run fails, GitHub emails the owner. A CI workflow runs the test suite on every push, including a new test that locks down which trading days a run fetches.

## User Stories
1. As a site visitor, I want the ratings to reflect the previous trading day each morning, so that what I see is current.
2. As the owner, I want the daily refresh to run without me doing anything, so that the site stays current when I'm busy or away.
3. As the owner, I want the refresh to run after Massive's free tier publishes the day, so that it doesn't run before the data exists.
4. As the owner, I want the refresh to run Tuesday to Saturday (UTC), so that each run picks up the trading day that just ended, including Friday's.
5. As the owner, I want a second, later run each of those mornings, so that a late Massive publish is caught up the same day instead of the next.
6. As the owner, I want a run with nothing new to fetch to finish quickly and cheaply, so that the retry run costs almost nothing.
7. As the owner, I want market holidays to cause no failures, so that I don't get false alerts.
8. As the owner, I want an email when a refresh fails, so that I know the site may be stale.
9. As the owner, I want two runs never to write to the database at the same time, so that an overlapping retry can't corrupt data.
10. As the owner, I want a run that hangs to be stopped after a fixed time limit, so that a stuck API call doesn't burn runner time indefinitely.
11. As the owner, I want the database URL and Massive key kept as GitHub secrets, so that credentials never end up in the repo or the logs.
12. As the owner, I want the refresh to use the same Supabase database the site reads from, so that a finished refresh shows up on the site immediately with no redeploy.
13. As the owner, I want the README to explain the schedule and why it runs overnight, so that future me doesn't "fix" it back to the close.
14. As the owner, I want the README to warn that GitHub turns off scheduled workflows after 60 days with no commits, and say how to turn it back on, so that a quiet period doesn't silently stop refreshes.
15. As the owner, I want the README's local instructions to say a new trading day is available after midnight ET, not "after the market closes", so that manual runs aren't attempted too early.
16. As the owner, I want a test proving that a Saturday run fetches Friday and a Tuesday run fetches Monday, so that a timezone or off-by-one mistake is caught before it ships.
17. As the owner, I want tests to run automatically on every push and pull request, so that breaking the RS math or the fetch window is caught without remembering to run pytest.
18. As the owner, I want the CI tests to need no secrets or database, so that they're fast and safe to run on any push.
19. As the owner, I want the idea of a manual "Run workflow" button recorded, so that I can add on-demand refreshes later without redoing the design.
20. As a future agent or contributor, I want the project's vocabulary (trading day, daily refresh, backfill, rated date) defined in one glossary, so that issues and code use the same words.

## Implementation Decisions
- **Scheduler**: GitHub Actions cron. Render cron jobs cost money, Supabase `pg_cron` can't run Python, and a laptop cron only runs while the laptop is awake.
- **Schedule**: two crons, 07:00 UTC and 13:00 UTC, Tuesday to Saturday. 07:00 UTC is 2 am EST / 3 am EDT, comfortably after Massive's end-of-day cutoff in both seasons. The 13:00 UTC run is the same-day retry. GitHub cron start times can drift by several minutes, and that's acceptable.
- **No manual trigger**: the workflow has only the schedule. On-demand runs are recorded in `docs/todo-ideas.md` as a future idea.
- **The ETL is unchanged apart from one extraction**: the daily refresh runs the existing ETL entry point unmodified. Its existing behaviour already suits unattended runs. It fetches only missing weekdays, commits each day, tolerates empty recent days within the three-day grace window, retries on rate limits, and is idempotent.
- **New pure function, the test seam**: pull the "which days still need fetching" calculation out of the price-fetch step. It takes today's date, the history window length in days, and the set of already-fetched dates, and returns the ordered weekdays from the start of the window up to yesterday that haven't been fetched. The price-fetch step calls it, and its behaviour doesn't change. The date source stays the process's local date, which is UTC on the runner. Local runs on the owner's machine are unaffected.
- **Refresh workflow**: checkout, install uv with a lockfile-keyed cache, sync production dependencies from the frozen lockfile, then run the ETL from the backend directory. Concurrency group `etl` with in-progress runs not cancelled, a 30-minute timeout, and read-only repository permissions.
- **Secrets**: `DATABASE_URL` (the Supabase session-pooler URL, the same one Render uses) and `MASSIVE_API_KEY`, read from the environment by the existing config. The owner enters the values. The agent never reads or prints `.env`.
- **Alerting**: GitHub's default failure email for scheduled workflows. A run that finds "no data yet" counts as a success, and the retry run plus the next night handle it.
- **CI test workflow**: runs on push and pull request. Checkout, install uv, sync with dev dependencies, run pytest from the backend directory. No secrets, no database.
- **Docs**: the README gains a Deployment section (Render web service with `DATABASE_URL` set in the dashboard, the daily refresh schedule and why, the secrets, the failure email, the 60-day auto-disable and re-enabling it, CI tests), and its "rerun after the market closes" line is corrected. A comment in the workflow explains the overnight timing.
- **No ADR**: the schedule and scheduler are cheap to reverse, so this fails the "hard to reverse" test. The reasoning goes in the README and the workflow comment. This doesn't conflict with ADR 0001 (Postgres): the refresh uses the same `DATABASE_URL` mechanism that ADR set up for this purpose.

## Testing Decisions
- **A good test checks behaviour you can see from outside**: which trading days a run will fetch for a given "today" and fetched set. It doesn't check how the price-fetch step loops or writes.
- **One seam**: the new pending-days function. It's pure, so the tests use no database, network or clock mocking; "today" is passed in.
- **Cases**:
  - A Saturday run (2026-11-07) ends at Friday 2026-11-06.
  - A Tuesday run (2026-11-10) ends at Monday 2026-11-09 and excludes the weekend.
  - Already-fetched dates are skipped.
  - A fully fetched window returns nothing.
  - The window start respects the days parameter.
- **Prior art**: the existing RS tests. These are plain pytest functions over the pure RS module with hand-built inputs; follow the same style in a new ETL test module.
- **Not unit-tested**: the workflow files. They're checked by linting with actionlint, by running the ETL command locally against Supabase, by the CI test workflow going green on push, and by the first scheduled refresh succeeding with the rated date on the live status endpoint equal to the previous trading day.

## Out of Scope
- A manual "Run workflow" trigger (recorded as an idea).
- Same-day data at the close, which would need a paid Massive plan and an ETL change to include today.
- Failing a run when the latest trading day is still missing, or any alerting beyond GitHub's email.
- A keepalive against the 60-day auto-disable.
- Integration tests of the price-fetch step against a real database.
- Changes to Render, the API, the frontend, or the database schema.
- An ADR for this decision.

## Further Notes
- The first proof that the refresh works end to end is the first scheduled 07:00 UTC run after the secrets are added. With no manual trigger, it can't be started sooner on GitHub.
- On the trading day after a market holiday, the holiday shows "no data yet" for up to three days and is then recorded as closed. That's expected and isn't an error.
- Next step: `/to-tickets` to split this into implementation tickets under `.scratch/daily-etl/issues/`.
