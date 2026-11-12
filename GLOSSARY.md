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

**Leader**:
One of the 50 highest-rated companies across the whole S&P 500 on the rated date. A sector filter never makes a company a Leader.
_Avoid_: Top stock, top pick

**Blurb**:
A short AI-written explanation of why a Leader is leading, as of one rated date.
_Avoid_: Brief, summary, report, research note

**Blurb run**:
A manual run that writes a Blurb for each current Leader. It is separate from the daily refresh.
_Avoid_: Research job, brief run

**Catalyst**:
A specific, dated event in the news that plausibly explains a Leader's move, such as a product launch, an earnings beat or a major contract. A plain analyst rating change is not a Catalyst.
_Avoid_: Driver, trigger

**Market direction**:
The state of the S&P 500 trend: Uptrend, Under pressure or Downtrend.
_Avoid_: Market trend, regime, market status
