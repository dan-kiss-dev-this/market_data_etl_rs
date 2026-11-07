# S&P 500 RS Ratings

Daily IBD-style relative-strength ratings for S&P 500 companies, computed from Massive price data.

## Language

**Trading day**:
A weekday on which the US stock market was open. Market holidays are weekdays but not trading days.
_Avoid_: Market day, business day

**Daily refresh**:
The scheduled, unattended ETL run that brings prices and ratings up to the latest trading day Massive has published.
_Avoid_: ETL update, nightly job, market-close update

**Backfill**:
An ETL run that fetches many trading days of history at once, such as the first run or a gap of several days.
_Avoid_: Initial load, full load

**Rated date**:
The latest trading day that has RS Ratings.
_Avoid_: Last updated, as-of date
