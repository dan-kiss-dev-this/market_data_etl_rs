# 03: Skeletons via Suspense and TanStack Query

**What to build:** Each area that loads data (the page before status, the leaders table, the chart card) shows its own skeleton on first load, rendered by a `<Suspense>` boundary where that component sits. Data comes from TanStack Query's `useSuspenseQuery` (`src/queries.ts`), and errors from `react-error-boundary`. Switching sector or stock keeps the old content visible and dimmed (`useDeferredValue`, `.is-loading`) instead of flashing a skeleton.

The presentational components keep taking data as props. Thin readers in `App.tsx` call the queries. The hand-written fetching effects, `cancelled` flags, `error` state and the 500ms minimum from `02` are removed.

**Blocked by:** 02

**Status:** ready-for-agent

- [x] Page skeleton until status and sectors load
- [x] Table and chart each show their own skeleton on first load
- [x] Switching sector or stock dims the old content until new data arrives; no skeleton flash
- [x] A failed request shows the "Could not load data" notice
- [x] `npm run build`, `npm test` and `npm run lint` pass

## Comments

Covered by `frontend/src/App.test.tsx` (test `QueryClient` with `retry: false`, mocked `api`), plus the skeleton and `stale` tests in the component test files. `queries.ts` calls `api.x()` inside a wrapper rather than storing `api.x` directly, so tests can swap the functions out.

Checked in the browser with `fetch` slowed to 4s: clicking a stock highlights its row at once, and the old chart stays up, dimmed, until the new one arrives. No console errors. The first-load skeletons were checked by tests only.

The full rewrite of `App.tsx` for this ticket dropped the AI Researcher wiring from `eed08db`, which was committed while the work was in progress. It is restored in `Chart` (it floats, so its place in the tree doesn't matter), and `App.test.tsx` now checks that the button appears for the charted stock.
