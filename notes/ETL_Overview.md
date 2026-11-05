# ETL Overview

Source: [etl.py](../backend/app/etl.py), [massive.py](../backend/app/massive.py), [db.py](../backend/app/db.py), [rs.py](../backend/app/rs.py). Run it by hand from `backend/` with `uv run python -m app.etl`. Nothing schedules it.

## Extract: what it pulls, and from where

There are two sources.

1. **The S&P 500 company list**: a CSV of about 500 rows from the `datasets/s-and-p-500-companies` repo on GitHub ([config.py](../backend/app/config.py)). It's fetched again in full on every run (`load_companies`).
2. **Daily prices from Massive** (formerly Polygon.io, at `api.massive.com`), with a Bearer key from `backend/.env`:
   - **Grouped daily**: one call per weekday returns every US stock's bar for that day (`grouped_daily`). It covers the last 725 calendar days, just inside the free tier's 2-year limit, and skips days already listed in `fetched_dates`. This is the main extract.
   - **Per-ticker range**: one ticker's full history. It's only used to rebuild history after a rename or a split.
   - **Ticker events**: symbol changes, for example BK → BNY.
   - **Splits**: every split since the earliest date in the database, following the pagination links.

The client waits 12.5 seconds between calls to stay under the free tier's 5 calls a minute. The first backfill takes about 1 hour 50 minutes, and later runs take seconds.

## Transform: what it changes

**Cleaning the prices:**

- It keeps only S&P 500 tickers plus `SPY`, the benchmark, and drops every other US stock.
- From each bar it keeps only **close and volume**. Open, high, low and VWAP are thrown away.
- Prices are requested split-adjusted (`adjusted=true`). Bars fetched before a split are stale, so if a split happened after some of a ticker's bars were fetched, its whole history is fetched again (`apply_splits`).
- **Renames**: a ticker gets its history rebuilt if it has more than 5 fewer bars than SPY, or if its close jumped more than 3× (or fell to under a third) from one day to the next (`fix_renames`). Bars traded under old symbols are joined together and stored under the current ticker. This also removes bars from an unrelated security that used the same symbol earlier.

**Computing the RS rating** ([rs.py](../backend/app/rs.py)). This is IBD-style relative strength, not RSI.

1. Every ticker's closes are lined up on SPY's trading dates.
2. **Weighted performance** = 0.4 × (close ÷ close 63 days ago) + 0.2 × each of the same ratio at 126, 189 and 252 trading days back.
3. `rs_score = 100 × stock performance ÷ SPY performance`.
4. Each day, `rs_rating` ranks the scores as a percentile from 1 to 99. Tied scores get the same rating.
5. It also calculates `ret_3m`, `ret_12m`, and `rs_new_high`. That last one is true when the RS line (close ÷ SPY) is at a 252-day high.

A day only gets ratings once SPY has at least 253 bars before it, and a ticker only gets a rating if none of its lookback closes are missing.

## Load: where it goes, and what the tables look like

Everything goes into one SQLite file, `backend/data/market.db`, in WAL mode so the API can read while the ETL writes ([db.py](../backend/app/db.py)). The `MARKET_DB` environment variable can point it somewhere else.

| Table | Key | Columns | How it's written |
|---|---|---|---|
| `companies` | `ticker` | `name`, `sector` | Deleted and re-inserted every run |
| `daily_bars` | `(ticker, date)` | `close REAL`, `volume REAL` | Upserted one day at a time; a ticker's rows are replaced when its history is rebuilt |
| `rs_ratings` | `(date, ticker)` | `rs_score REAL`, `rs_rating INT`, `ret_3m REAL`, `ret_12m REAL`, `rs_new_high INT` (0/1), plus an index on `(ticker, date)` | Deleted and fully recomputed every run |
| `fetched_dates` | `date` | `rows`, `fetched_at` | Tracks which days are done; holidays are stored with `rows = 0` |
| `splits_applied` | `(ticker, execution_date)` | | Tracks which splits have been handled |
| `history_checked` | `ticker` | `checked_at` | Tracks which tickers have had a rename check |

`rs_ratings` is the table the API reads. The last three only exist so the ETL can tell what it has already done.

## Failure: what happens if a run fails

**What protects it:** each piece of work is committed in its own transaction and marked as done only after it succeeds. That means a crash keeps everything finished up to that point, and running it again picks up where it stopped.

- **Rate limit (HTTP 429)**: it waits 60 seconds and retries with no limit. This is the only automatic retry.
- **Another HTTP error on one day** (for example a 403 for a date outside the plan's history): that day is skipped and not marked, so the next run tries it again.
- **No data for a day in the last 3 days**: it isn't marked, because Massive may not have published it yet.
- **A crash anywhere else** (network error, timeout, a 5xx while rebuilding a rename or split): the run stops with a traceback and a non-zero exit code.
  - Days already fetched stay saved.
  - A ticker's history is fully downloaded before its old rows are deleted, so a failed rebuild leaves the old bars in place.
  - `rs_ratings` is deleted and re-inserted in one transaction, so the API keeps serving the previous ratings. They're stale, but consistent.
  - You recover by running it again. `--rs-only` recomputes the ratings without calling the API.

**Weak spots:**

- **Nothing alerts you.** There's no scheduler and no notification, and skipped days only appear as printed lines. A run that skips days still exits 0.
- **One bad ticker blocks everything after it.** The rename and split rebuilds don't catch errors for each ticker separately, and they run before the RS step. If one ticker keeps failing, every run crashes there, and splits and ratings stop updating until someone notices.
- **A missing day can be mistaken for a holiday.** If Massive returns an empty result for a day more than 3 days old, it's recorded as "market closed" (`rows = 0`) and never fetched again. A real gap in Massive's data would be skipped for good.
- **The company list is a single point of failure.** If the GitHub CSV can't be fetched, the run stops before fetching any prices. The `companies` table rolls back to its previous contents, so it isn't emptied.
