# 02: Market direction from SPY closes

**What to build:** A `market_direction(conn, date)` function in `backend/app/market.py` that reads SPY closes (and every company's closes, for breadth) from `daily_bars` up to `date`. It returns the close, the 50-day and 200-day moving averages, whether the 50-day average is rising (compared with 10 trading days earlier), the 1-month and 3-month returns, breadth (the % of companies whose close is above their own 50-day average), and a `status`:
- **Uptrend** when close > 50-day average > 200-day average
- **Downtrend** when close < 200-day average and the 50-day average is falling
- **Under pressure** otherwise

Breadth doesn't affect the status. See `../spec.md`.

**Blocked by:** None (can start immediately)

**Status:** done

- [x] `market_direction` returns the fields above for a given rated date
- [x] The status rule matches the definition above, including the edge cases between states
- [x] Unit tests cover made-up uptrend, downtrend and choppy series
- [x] `uv run pytest` passes

## Comments
