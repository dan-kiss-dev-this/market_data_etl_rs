# 03: Half-width RS Rating bar on mobile

**What to build:** On phone-width screens (480px and below), make the blue RS Rating bar in the leaders table half as wide: 24px instead of 48px. Its height and the filled share (rating out of 99) stay the same. Wider screens don't change. CSS only: a `.meter` rule in the same 480px media query in `frontend/src/index.css` as tickets 01 and 02.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] At 375×667, the RS Rating bar is 24px wide and still fills in proportion to the rating
- [ ] Above 480px, the bar is still 48px wide
- [x] `npm run build` passes

## Comments

The first version didn't work: the mobile `.meter` rule came before the base `.meter` rule in `index.css`. Both have the same specificity, so the later 48px rule won. Fixed by moving the whole 480px media query to the end of the leaders-table section, after every rule it overrides.
