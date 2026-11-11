# 04: No layout shift on first load

**What to build:** On first load, `header.app-header` and `div.filters` render only after `status` and `sectors` arrive, so they push the table and chart down. Render the page frame at once and suspend only the data leaves:

- Header: the title and copy render immediately. The benchmark name and the ratings date each sit in their own `<Suspense>`, with a word-sized shimmer as the fallback.
- Filters: the bar, range picker and legend render immediately. The sector `<select>` sits in its own `<Suspense>`, with a disabled select of the same size as the fallback.
- Start `sectors` and `leaders` fetching on mount (`usePrefetchQuery`) instead of after `status`, so the loads run in parallel.
- The "No RS ratings yet" notice still replaces the filters and layout once status says so.

**Blocked by:** 03

**Status:** ready-for-agent

- [x] Header and filters are on screen, in their final size, before any data arrives
- [ ] Benchmark, date and sector select fill in without moving anything
- [x] Sectors and leaders start fetching without waiting for status
- [x] `npm run build`, `npm test` and `npm run lint` pass

## Comments

The loaded sector `<select>` sizes to its longest option ("Communication Services", 212px), while the one-option placeholder was 114px. `.filters select { min-width: 15rem }` makes both the same width.

Covered by `frontend/src/App.test.tsx`: frame and skeletons before status loads, benchmark/date/select filling in, and sectors+leaders fetched before status resolves. Not yet confirmed in the browser that nothing moves: the browser tool refused to run scripts on the page, so layout shift was never measured.
