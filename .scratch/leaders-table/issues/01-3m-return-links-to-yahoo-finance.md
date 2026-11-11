# 01: 3M return links to the Yahoo Finance chart

**What to build:** In the leaders table, make each row's 3M return a link to `https://finance.yahoo.com/quote/<TICKER>/` (e.g. MRNA → `https://finance.yahoo.com/quote/MRNA/`), opening in a new tab (`target="_blank" rel="noopener noreferrer"`). The row is itself clickable and keyboard-selectable, so the link stops `click` and `keydown` from reaching the row. Without that, the row would select the stock, and its Enter handler's `preventDefault` would stop the link from opening. The ticker is URL-encoded so tickers like `BRK.B` or `BF-B` still build a valid URL.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Clicking a 3M return opens that ticker's Yahoo Finance quote page in a new tab, and the selected row doesn't change
- [ ] Tabbing to the link and pressing Enter opens it too
- [ ] Clicking anywhere else in the row still selects it
- [x] `npm run build` passes

## Comments

Covered by `frontend/src/components/LeadersTable.test.tsx` (runs in the existing `vitest` CI job). It checks the href, `target`/`rel`, URL-encoding of the ticker, that clicking the 3M return doesn't select the row, that Enter on the 3M return isn't `preventDefault`-ed by the row, and that clicking elsewhere still selects. Removing the `stopPropagation` calls fails the two event tests. The click and keyboard items above still need a manual check in a browser, because jsdom doesn't really open a new tab.

The link was first put on the Close price, then moved to the 3M return at the user's request. Close is plain text again, and a test checks that the table has only one link per row.
