# Market Data ETL and RS with FastAPI + React

## Running it

Start the backend and the frontend in separate terminals. Each command block starts from the project root.

**Terminal 1: backend**
```bash
cd backend
uv run fastapi dev app/main.py   # http://localhost:8000, docs at /docs
```

**Terminal 2: frontend**
```bash
cd frontend
npm run dev   # http://localhost:5173
```

Open http://localhost:5173. Vite forwards `/api` requests to the backend on port 8000.

## Data pipeline (S&P 500 RS Ratings)

The ETL pulls daily S&P 500 prices from [Massive](https://massive.com) (formerly Polygon.io) and computes IBD-style RS Ratings into Postgres. See `notes/setup2_pipeline.md` for the method.

0. Have Postgres running locally ([Postgres.app](https://postgresapp.com)) and create the database once: `createdb -U postgres market`. This is the dev database, and every local command uses it by default (see [Dev and production](#dev-and-production)). To browse the data, double-click `market` in Postgres.app or use a GUI like TablePlus.

1. Get a free Massive API key and add it to `backend/.env` (template: `backend/.env.example`):
   ```
   MASSIVE_API_KEY=your-key
   ```
2. Run the pipeline from `backend/`:
   ```bash
   uv run python -m app.etl            # first run: ~2 years of history, about 1 h 50 min
   uv run python -m app.etl            # later runs: only the missing days, a few seconds each
   uv run python -m app.etl --rs-only  # recompute ratings without calling the API
   ```
   The free tier allows 5 calls a minute, and each trading day takes one call. Every day is saved as soon as it arrives, so you can stop the run at any point and rerunning resumes it. Massive's free tier only serves a trading day after that day has ended, so rerun it after midnight ET to add the new day; the run fetches up to yesterday by your machine's date.
3. Run the tests from `backend/` with `uv run pytest`. They also run in CI on every push and pull request (`.github/workflows/test.yml`); they need no secrets or database.

## Blurb run (AI Researcher)

The AI Researcher panel shows a **Blurb** for each Leader (the 50 highest-rated companies): why it's leading, written by Claude Haiku from the company's description, RS data, the last 30 days of Massive news and the Market direction. You run it by hand, about weekly. A full run costs about $0.03 in API fees and takes about 10 minutes because of Massive's rate limit. See `.scratch/ai-researcher/spec.md`.

The news comes only from the Blurb run. It fetches the Leader's last 30 days of Massive news, and Haiku picks up to 3 headlines that support the Catalyst, by number. The run saves those real headlines with the Blurb, and the panel lists them under Sources, linking to the articles. Haiku can't add a headline or a link of its own. Chat with AI answers from these saved headlines and makes no news call of its own, so its news is only as fresh as the latest Blurb run.

1. Add an Anthropic API key to `backend/.env`:
   ```
   ANTHROPIC_API_KEY=your-key
   ```
2. Run it from `backend/`. Without `--env-file` it writes to the local dev database:
   ```bash
   uv run python -m app.blurbs --limit 3                                 # try a few Leaders
   uv run python -m app.blurbs --ticker NVDA                             # one Leader
   uv run --env-file .env.production python -m app.blurbs               # publish to the live site
   ```
   Rerunning on the same rated date replaces that date's Blurbs. A Leader that fails is skipped and listed at the end. The run only exits with an error if more than 10 fail. The panel shows a Blurb for 7 days after its rated date.

**Don't start a Blurb run while the Daily refresh may be running: 07:00–07:45 or 13:00–13:45 UTC, Tuesday to Saturday.** Both use the same Massive key, which allows 5 calls a minute in total, so running them together slows both down and can push the refresh past its 30-minute timeout. The Blurb run refuses to start in those windows. Pass `--force` if you know the refresh has already finished.

## Chat with AI

The AI Researcher panel lets a visitor ask follow-up questions about a Leader. Claude Haiku answers only from stored data: the Leader's Blurb and the headlines it cites, RS data, company description and Market direction. It runs no web search and makes no Massive call per message, and replies stream in. See `.scratch/chat-with-ai/spec.md`.
- **Only for Leaders:** chat works only for companies with a current Blurb. Other companies show a disabled input.
- **Limits** (in `backend/app/config.py`): each visitor gets 5 messages per UTC day, of up to 250 characters each, and the whole site gets 100 a day. Visitors are anonymous and are identified by a hash of the day and their IP. No IP is stored.
- **Cost:** about $0.001 a message, so the site cap holds spending to about $0.11 a day. As a backstop, set a monthly spend limit in the Anthropic Console.
- **Setup:** chat uses the same `ANTHROPIC_API_KEY` as the Blurb run, plus a `chat_usage` table that the ETL creates. Without the key or the table, the endpoint returns 503 and the panel shows chat as unavailable. On Render, enter the key in the dashboard (`render.yaml` declares it with `sync: false`).

## Dev and production

There are two databases:
- **Dev:** local Postgres.app (`market`). It's the default for every command run from `backend/`.
- **Production:** Supabase. The live site and the Daily refresh use it.

Its URL lives only in `backend/.env.production` (gitignored), as `DATABASE_URL=<supabase session-pooler url>`, and is used only when you pass that file:

```bash
uv run fastapi dev app/main.py                                    # dev: local Postgres
uv run --env-file .env.production fastapi dev app/main.py         # the local app on production data
uv run python -m app.pull_prod                                    # bring dev up to date with production
```

`app.pull_prod` only reads from Supabase. It copies only what dev is missing:
- new `daily_bars` days
- the full history of any ticker whose past bars changed (a split or a rename)
- the small tables: companies, Blurbs, Market directions and descriptions

Then it rebuilds RS ratings locally. Chat message counts aren't copied. It takes a few seconds and is safe to rerun.

## Deployment

**Site:** one Render web service (`render.yaml`) builds `deploy/Dockerfile` and serves the API and the built frontend. It redeploys on every push to `main`. Its `DATABASE_URL`, the Supabase session-pooler URL, is entered in the Render dashboard and never committed.

**Daily refresh:** `.github/workflows/daily-refresh.yml` runs the ETL against the same Supabase database at 07:00 UTC and 13:00 UTC, Tuesday to Saturday. The site picks up new ratings straight away, with no redeploy. By US morning it shows the previous trading day.
- It runs overnight, not at the close, because Massive's free tier only serves a trading day after it has ended, and the ETL fetches up to yesterday by the runner's UTC date. A run at the close would always be a day behind. 07:00 UTC is 2 am EST / 3 am EDT.
- The 13:00 UTC run retries in case Massive published late. When there's nothing new it finishes in seconds.
- A market holiday shows as "no data yet" for up to three days and is then recorded as closed. That isn't a failure.
- It reads two repository secrets, `DATABASE_URL` and `MASSIVE_API_KEY`. Set or replace them with `gh secret set <NAME>`, which prompts for the value.
- **`DATABASE_URL` must be Supabase's Session pooler URL** (`…@aws-0-<region>.pooler.supabase.com:5432/postgres`), not the direct-connection host `db.<ref>.supabase.co`. The direct host only has an IPv6 address, and GitHub runners have no IPv6, so the run fails with `Network is unreachable`. A local run can still work because your machine may have IPv6. Use the pooler URL in Render and `backend/.env.production` too.
- If a run fails, GitHub emails the repo owner. There's no other alerting.
- There's no manual trigger. To refresh on demand, run the ETL locally against production: `uv run --env-file .env.production python -m app.etl`.
- **GitHub turns off scheduled workflows after 60 days with no commits to the repo.** To turn it back on, open the repo's Actions tab, pick "Daily refresh" and click "Enable workflow", or run `gh workflow enable daily-refresh.yml`.

**CI:** `.github/workflows/test.yml` runs pytest, Vitest and actionlint on every push and pull request. It needs no secrets.

## Adding dependencies

Run the backend commands from `backend/` and the frontend commands from `frontend/`.

| | Add | Add (dev) | Remove | Fresh install |
|---|---|---|---|---|
| Backend | `uv add X` | `uv add --dev X` | `uv remove X` | `uv sync` |
| Frontend | `npm install X` | `npm install -D X` | `npm uninstall X` | `npm ci` |

Commit the lockfiles (`backend/uv.lock` and `frontend/package-lock.json`) along with the manifests. On the backend, use `uv` and never bare `pip`. Packages go into `backend/.venv/`, so your global Python stays untouched.
