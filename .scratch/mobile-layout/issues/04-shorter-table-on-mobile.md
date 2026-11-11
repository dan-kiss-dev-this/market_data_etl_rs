# 04: Shorter leaders table on mobile

**What to build:** On phone-width screens (480px and below), cap the leaders table's scroll area (`.table-wrap`) at 300px tall instead of 760px, so the chart below it is reachable without scrolling far. The table still scrolls inside its box, and the header row stays sticky. Wider screens don't change. CSS only: a `.table-wrap` rule in the mobile overrides media query at the end of the leaders-table section in `frontend/src/index.css` (see ticket 03 for why it has to be there).

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] At 375×667, the table box is at most 300px tall and scrolls inside, with the header row staying visible
- [ ] Above 480px, the table box is still up to 760px tall
- [x] `npm run build` passes
