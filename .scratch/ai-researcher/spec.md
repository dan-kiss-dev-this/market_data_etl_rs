# AI Researcher: weekly Blurbs for the Leaders

Status: ready-for-agent

## Problem Statement
The AI Researcher panel is a placeholder that says "Service Not Available". The site is built for momentum trading: high-RS stocks with new products that lead their category. A generic company description doesn't help with that. The owner wants the panel to explain, in a few lines, why a Leader is leading, at close to no cost.

## Solution
Once a week the owner runs a local **Blurb run**. For each of the 50 Leaders it collects the company description and recent news from Massive, adds the Leader's RS data and the Market direction from Postgres, and asks Claude Haiku 5.5 for a short **Blurb** with five fixed fields. Blurbs are saved in Postgres. When the panel opens, it reads the saved Blurb, so there's never an AI call per click. A run costs about $0.03. Speed is limited by the Massive free plan's 5 calls a minute.

## User Stories
1. As a trader, I want the panel to show why a Leader is leading (its Catalyst, category position and momentum), so that I can judge the setup quickly.
2. As a trader, I want to see the Market direction next to each Blurb, so that I don't act on a strong setup in a Downtrend.
3. As a trader, I want the Catalyst to cite up to 3 linked headlines, so that I can check the source.
4. As a trader, I want "No clear Catalyst in recent news" instead of a guess, so that I can trust what's written.
5. As a trader, I want each Blurb to show its date, and the panel to stop showing a Blurb once it's more than 7 days old, so that I never mistake old research for current.
6. As a trader, I want a clear "No current Blurb. Blurbs cover the top 50 by RS rating." for companies that aren't Leaders.
7. As the owner, I want to start the Blurb run myself, locally, against whatever `DATABASE_URL` is set, so that I control the cost and can test it on local Postgres.
8. As the owner, I want the Blurb run to refuse to start during the Daily refresh windows unless I pass `--force`, with a red message saying why, so that the two runs don't compete for the Massive rate limit.
9. As the owner, I want a warning when the rated date is more than 3 trading days old, so that I notice a broken Daily refresh.
10. As the owner, I want a failed Leader to be skipped and listed, and the run to fail only if more than 10 fail, so that one bad response doesn't waste the whole run.
11. As the owner, I want running again on the same rated date to replace that date's Blurbs, so that I can rerun after changing the prompt.

## Implementation Decisions
- **Leader**: the top 50 by `rs_rating DESC, rs_score DESC` on the rated date, across the whole S&P 500, ordered the same way as `/api/rs/leaders`.
- **Context per Leader:**
  - the company description from Massive `/v3/reference/tickers/{t}`, saved on `companies` and re-fetched after 90 days
  - RS rating, 1-week change, RS new high, 3-month and 12-month returns, and rank within its sector
  - up to 10 Massive news headlines from the 30 days ending on the rated date
  - the Market direction
- **Market direction** is computed from SPY closes in `daily_bars`:
  - Uptrend if close > 50-day average > 200-day average
  - Downtrend if close < 200-day average and the 50-day average is falling (compared with 10 trading days ago)
  - Under pressure otherwise

  Breadth (the % of companies above their own 50-day average) is shown for information only.
- **Model:** `claude-haiku-5-5` at low effort. It returns structured output with the fields `what_they_sell`, `catalyst`, `catalyst_sources`, `category_position`, `momentum`, `risks`. It may use general knowledge for What they sell and Category position. The Catalyst must come only from the numbered headlines it was given.
- **Storage:**
  - `blurbs (ticker, date)` holds the Blurb, the cited headlines and the model, and is upserted on rerun
  - `market_directions (date)` holds that day's market snapshot
- **Startup guard:** 07:00–07:45 and 13:00–13:45 UTC, Tue–Sat, which match the Daily refresh schedule in `.github/workflows/daily-refresh.yml`.
- **Endpoint:** `GET /api/rs/{ticker}/blurb` returns the latest Blurb if it is at most 7 days old, with that date's Market direction. Otherwise it returns 404.

## Testing Decisions
- `market_direction` is tested on made-up uptrend, downtrend and choppy series.
- The Blurb run is tested with Massive and Anthropic mocked: Leader selection, the 90-day description refresh, skipping failed Leaders and the more-than-10 rule, the guard windows and `--force`, and reruns replacing Blurbs.
- The endpoint is tested for a fresh Blurb, a Blurb more than 7 days old, and a missing one. The panel is tested for loading, success and 404.

## Out of Scope
- Chatting with the AI Researcher. The input stays disabled.
- Scheduling the Blurb run, or running it in GitHub Actions.
- Blurbs for companies that aren't Leaders.
- A quantitative Market direction report (see `docs/todo-ideas.md`).

## Further Notes
Massive's news endpoint needs checking against the free plan before slice 03 is built.
