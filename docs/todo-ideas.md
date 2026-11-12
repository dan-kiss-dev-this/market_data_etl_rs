# Ideas

Things we decided not to build yet, with enough context to pick them up later.

## High priority: turn on ChatWithAI in production (Anthropic API key in Render)

The live site's chat stays disabled ("Chat isn't available right now") until the Render service has an Anthropic key. `render.yaml` already lists `ANTHROPIC_API_KEY` with `sync: false`, so the value has to be entered by hand:
1. In the Render dashboard, open the `market-rs` service, then Environment, and add `ANTHROPIC_API_KEY`. Saving it redeploys the service.
2. Set a monthly spend limit in the Anthropic Console (for example $10) as a backstop. The site already caps chat at 5 messages per visitor and 100 a day, about $0.11/day at most.
3. Make sure the `chat_usage` table exists in Supabase. The first Daily refresh after the chat code is on `main` creates it, or run `uv run --env-file .env.production python -m app.etl` once.
4. Check on the live site: a Leader's reply streams, the counter goes down, and a non-Leader shows the disabled input.

Full checklist: `.scratch/chat-with-ai/issues/03-deploy-chat.md`.

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
