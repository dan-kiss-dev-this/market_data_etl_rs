# 02: Whole-number 3M and 12M returns on mobile

**What to build:** On phone-width screens (480px and below), show the leaders table's 3M and 12M returns rounded to the nearest whole percent, so +22.5% reads +23%. Round half away from zero (-22.5% reads -23%), working from the one-decimal value shown on desktop. Wider screens keep one decimal. `LeadersTable.tsx` renders both forms and CSS in `index.css` shows one per breakpoint, in the same 480px media query as ticket 01.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] At 375×667, 3M and 12M show whole percents (e.g. +22.5% → +23%, -22.5% → -23%)
- [ ] Above 480px, 3M and 12M still show one decimal
- [ ] Screen readers read only the visible value
- [x] `npm run build` passes
