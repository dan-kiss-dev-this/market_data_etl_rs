# Define the Market direction at the bottom of the Blurb

Status: ready-for-agent

The panel shows "S&P 500 on {date}: Under pressure" but never says what that means. Add a one-line definition of the current Market direction at the bottom of the Blurb, after the sources, for example "Under pressure: the S&P 500 is neither in an Uptrend nor a Downtrend." Add Uptrend, Under pressure and Downtrend to `GLOSSARY.md`, worded to match the rule in `backend/app/market.py`.

## Acceptance

- [x] A Vitest test in `AiResearcher.test.tsx` checks that the definition of the shown Market direction is the last thing in the Blurb
- [x] The panel shows the definition for whichever of the three states is current, and nothing when there's no Market direction
- [x] `GLOSSARY.md` has Uptrend, Under pressure and Downtrend entries
- [x] Spec updated

## Comments
- vitest 48/48 passing, tsc clean, 2026-11-24.
