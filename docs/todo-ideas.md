# Ideas

Things we decided not to build yet, with enough context to pick them up later.

## Manual "Run workflow" button for the daily refresh

Add a `workflow_dispatch` trigger to `.github/workflows/daily-refresh.yml` so a refresh can be started on demand from the Actions tab or with `gh workflow run daily-refresh.yml`. Left out at first to keep the workflow schedule-only (see `.scratch/daily-etl/spec.md`). The existing `etl` concurrency group already stops a manual run from overlapping a scheduled one, so the change is one trigger line plus a README note.

## How long a Blurb stays current

The AI Researcher panel shows a Leader's latest Blurb only if it is at most 7 days old (see `.scratch/ai-researcher/spec.md`). The 7 days was picked to match a weekly Blurb run. Revisit it once we've seen how often the run actually happens: a missed week currently means former Leaders show "No current Blurb".

## Market direction, in more depth

Market direction uses a simple rule on SPY's 50-day and 200-day moving averages, and breadth is shown for information only. Ideas to look into:
- a quantitative Market direction report: how often each state occurred, how Leaders performed in each, and how long states lasted
- whether breadth or a distribution-day count should feed into the state

## News window counted from the rated date

The Blurb run reads news from the 30 days ending on the rated date, not ending today. That keeps the news in line with the prices a Blurb describes. But when the data is several days behind, the latest headlines are left out. Revisit this if stale data turns out to be common.
