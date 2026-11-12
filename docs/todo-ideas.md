# Ideas

Things we decided not to build yet, with enough context to pick them up later.

## Manual "Run workflow" button for the daily refresh

Add a `workflow_dispatch` trigger to `.github/workflows/daily-refresh.yml` so a refresh can be started on demand from the Actions tab or with `gh workflow run daily-refresh.yml`. Left out at first to keep the workflow schedule-only (see `.scratch/daily-etl/spec.md`). The existing `etl` concurrency group already stops a manual run from overlapping a scheduled one, so the change is one trigger line plus a README note.
