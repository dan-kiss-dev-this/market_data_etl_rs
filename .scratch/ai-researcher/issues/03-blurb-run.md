# 03: Blurb run

**What to build:** A local command, `uv run python -m app.blurbs`, with the options `--limit`, `--ticker` and `--force`. It writes a Blurb for each Leader on the latest rated date. Full design in `../spec.md`.

**Blocked by:** 02

**Status:** ready-for-agent

- [x] Step 0: one call to `/v2/reference/news` confirms the Massive free plan includes news. If it doesn't, stop and ask the owner
- [x] `MassiveClient.ticker_details` and `ticker_news` (30 days ending on the rated date, up to 10 headlines)
- [x] Schema: `companies.description` and `description_fetched_at`, plus the `blurbs` and `market_directions` tables
- [x] Startup guard: refuses to start 07:00–07:45 and 13:00–13:45 UTC, Tue–Sat, with a red message, unless `--force` is passed
- [x] Warns, and carries on, when the rated date is more than 3 trading days old
- [x] Descriptions are re-fetched when they are more than 90 days old
- [ ] Haiku 5.5 at low effort returns the 5 structured fields plus `catalyst_sources`. Only the cited headlines (up to 3) are stored
- [x] Reruns replace that date's Blurb. Failed Leaders are skipped and listed. The run exits non-zero if more than 10 fail
- [x] The README covers the local and production commands, plus the warning about the Daily refresh time windows
- [x] Tests with Massive and Anthropic mocked. `uv run pytest` passes

## Comments

- Step 0 passed: the Massive free plan includes `/v2/reference/news`. Massive tags an article with every ticker it mentions, so `ticker_news` fetches 50 articles in one call and keeps those that have an insight about the Leader and mention 5 tickers or fewer, most focused first. Haiku gets each headline plus Massive's insight about that Leader.
- Descriptions live in a new `company_profiles` table, not on `companies`: `load_companies` in `etl.py` deletes and re-inserts `companies` on every Daily refresh, which would wipe them.
- First real run (owner, 2026-11-12, against production): all 50 Leaders for 2026-11-10 were written in about 20 minutes with none skipped. 41 have a cited Catalyst, almost all earnings beats or raised guidance. The other 9 (including MU and CRWD) say "No clear Catalyst in recent news", which is correct: their news in the window is all opinion pieces.
- The prompt was changed after that run. All 50 Momentum fields ended with the same warning about the market, because the prompt asked for it. 46 Category position fields used the RS sector rank as if it were a category position. Momentum now leaves out the Market direction unless the stock is acting against it, and Category position names the product category and its rivals.
- Open: rerun a few Leaders with the new prompt and check those two fields, then tick the Haiku box.
