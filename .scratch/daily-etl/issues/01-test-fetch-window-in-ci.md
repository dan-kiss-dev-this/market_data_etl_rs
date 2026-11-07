# 01: Test the fetch window in CI

**What to build:** Pull the "which trading days still need fetching" calculation out of the price-fetch step into a pure function. It takes today's date, the history window length in days, and the set of already-fetched dates, and returns the weekdays, in order, from the start of the window up to yesterday that haven't been fetched. The price-fetch step calls it and behaves exactly as before; its date source stays the process's local date, which is UTC on GitHub's runners. Cover the function with tests in the style of the existing RS tests (plain pytest functions, no database, network or clock mocking). Add a CI workflow that runs the whole pytest suite on every push and pull request, needing no secrets or database. Mention the CI run in the README's tests note.

See the spec: `.scratch/daily-etl/spec.md` (Testing Decisions).

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] The price-fetch step uses the new function, and a local ETL run behaves as before (it reports "Prices: up to date" or fetches only the missing days)
- [x] Test: a run on Saturday 2026-11-07 ends at Friday 2026-11-06
- [x] Test: a run on Tuesday 2026-11-10 ends at Monday 2026-11-09 and excludes the weekend
- [x] Test: already-fetched dates are skipped, and a fully fetched window returns nothing
- [x] Test: the window start respects the days parameter
- [x] `uv run pytest` passes locally (existing RS tests and the new tests)
- [ ] The CI workflow runs on push and pull request, uses the frozen lockfile with dev dependencies, and goes green on GitHub
- [x] The README's tests note says the tests also run in CI
