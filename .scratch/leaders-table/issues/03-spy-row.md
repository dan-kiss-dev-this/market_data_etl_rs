# 03: SPY row pinned at the top of the leaders table

**What to build:** A row for the benchmark (SPY) at the top of the leaders table, above the Leaders, so each stock's 3M and 12M return can be compared with the S&P 500's. It shows SPY's close, 3M and 12M return as of the rated date, with `–` for rank, RS Rating and 1W. It is not numbered and does not count toward the 50 Leaders, and it stays when the sector filter changes. Clicking it (or Enter/Space) shows SPY's chart. That chart shows only the Price panel, because SPY's RS line against itself is flat and SPY has no RS Rating. The AI Researcher is hidden for SPY, since only Leaders get a Blurb.

Backend: `GET /api/rs/benchmark` returns `{ticker, name, date, close, ret_3m, ret_12m}` for the rated date (404 before the first ratings). The returns use the same 63- and 252-trading-day lookbacks as the Leaders' (`rs.period_returns`). `GET /api/rs/SPY` returns SPY's price series, even though SPY isn't in `companies`.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] Tests first: `backend/tests/test_rs.py` (period returns), `backend/tests/test_benchmark.py` (both endpoints), `frontend/src/components/LeadersTable.test.tsx` (SPY row), `frontend/src/components/RsChart.test.tsx` (price-only chart for SPY)
- [ ] SPY row is at the top of the table with its close, 3M and 12M, and no rank, rating or 1W
- [ ] Clicking the SPY row shows SPY's price chart, without RS panels or the AI Researcher
- [x] The SPY row stays in view under the header while the Leaders scroll
- [ ] Changing the sector keeps the SPY row, and keeps SPY selected if it was
- [x] `npm run build` passes

## Comments

Covered by `backend/tests/test_rs.py` (`period_returns`), `backend/tests/test_benchmark.py` (both endpoints, over a fake database), `frontend/src/components/LeadersTable.test.tsx` (SPY row contents and selection), `frontend/src/components/RsChart.test.tsx` (Price panel only) and `frontend/src/App.test.tsx` (clicking SPY charts it, with no AI Researcher). Each test failed before the code was written. Both endpoints were also checked against the local database. The row and chart items above still need a look in a browser.

The SPY row now sticks under the header (changed at the user's request; at first it scrolled with the table). Its cells are `position: sticky` at `--leaders-head-height`, which is the header's 10px + 16px line-height + 10px. A test in `LeadersTable.test.tsx` reads `index.css` and fails if the header padding or line-height changes without that variable. Its divider is a shadow, because collapsed borders don't stick.

In the browser, the Leaders showed through a stripe about 1px tall between the header and the SPY row. The header's `border-bottom` was a collapsed border, which is painted with the table and scrolled away from the sticky header. It is now an inset box-shadow, and the test checks that the header has no `border-bottom`. Checked in Chrome: no gap while scrolled, and the header line stays put.
