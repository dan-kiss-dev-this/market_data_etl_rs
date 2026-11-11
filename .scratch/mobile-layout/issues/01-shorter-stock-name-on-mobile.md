# 01: Shorter stock name on mobile

**What to build:** On phone-width screens (iPhone SE, 375px), the leaders table's Stock column is too wide because the company name under the ticker is only cut off at 22 characters. Below 480px, cut the name off with "…" at about 10 characters. Keep the ticker and the 52-week-high dot as they are. Desktop and tablet widths don't change. Use CSS only (a `max-width: 480px` media query on `.name` in `frontend/src/index.css`). The markup in `LeadersTable.tsx` doesn't change.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] At 375×667, company names are cut off with "…" at about 10 characters
- [ ] At 375×667, the ticker and the new-high dot still show in full
- [ ] Above 480px, names are still cut off at 22 characters as before
- [x] `npm run build` passes

## Comments

Out of scope: with 7 columns, the table may still scroll sideways at 375px. A follow-up could hide 3M/12M/Close on mobile.
