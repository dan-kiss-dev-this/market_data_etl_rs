# 02: Skeleton on first page load

**What to build:** When the site first loads, show the same chart skeleton as `01` (three panel skeletons at the chart heights, each with the dark yellow bolt) in place of the "Loading…" text. It stays up for at least 500ms, and longer if `/api/rs/status` hasn't answered yet. A load error still replaces it straight away.

`RsChart.tsx` exports a `ChartSkeleton` built from the same `PanelSkeleton` that `Panel` uses while loading, so the two can't drift apart. `App` keeps a 500ms timer from mount.

**Blocked by:** 01

**Status:** ready-for-agent

- [x] The skeleton shows immediately on load and for at least 500ms
- [x] The app renders once 500ms have passed and status has loaded
- [x] An error shows without waiting for the 500ms
- [x] `npm run build` and `npm test` pass

## Comments

Covered by `frontend/src/App.test.tsx` (mocked `api`, fake timers): skeleton at 0 and 499ms then the app at 500ms; skeleton held past 500ms until status resolves; an error shows at once.

The 500ms minimum was removed in `03`: it only added latency. The first-load skeleton now lasts exactly as long as the data takes.
