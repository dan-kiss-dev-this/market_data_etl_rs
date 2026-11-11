# 01: Close price links to the Yahoo Finance chart

**What to build:** In the leaders table, make each row's Close price a link to `https://finance.yahoo.com/quote/<TICKER>/` (e.g. MRNA → `https://finance.yahoo.com/quote/MRNA/`), opening in a new tab (`target="_blank" rel="noopener noreferrer"`). The row is itself clickable and keyboard-selectable, so the link stops `click` and `keydown` from reaching the row. Without that, the row would select the stock, and its Enter handler's `preventDefault` would stop the link from opening. The ticker is URL-encoded so tickers like `BRK.B` or `BF-B` still build a valid URL.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Clicking a Close price opens that ticker's Yahoo Finance quote page in a new tab, and the selected row doesn't change
- [ ] Tabbing to the link and pressing Enter opens it too
- [ ] Clicking anywhere else in the row still selects it
- [x] `npm run build` passes

## Comments

Covered by `frontend/src/components/LeadersTable.test.tsx` (runs in the existing `vitest` CI job). It checks the href, `target`/`rel`, URL-encoding of the ticker, that clicking the price doesn't select the row, that Enter on the price isn't `preventDefault`-ed by the row, and that clicking elsewhere still selects. Removing the `stopPropagation` calls fails the two event tests. The click and keyboard items above still need a manual check in a browser, because jsdom doesn't really open a new tab.
