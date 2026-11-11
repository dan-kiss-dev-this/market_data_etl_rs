# 01: Skeleton loader in chart panels while a ticker loads

**What to build:** While `RsChart` is `loading` (a new ticker's detail is in flight), each `figure.panel` keeps its caption but swaps its chart for a skeleton block of the same height, with a shimmer. The panels keep their size, so the card doesn't jump. The stale ticker header stays dimmed with `.is-loading`; the section gets `aria-busy`. The shimmer stops under `prefers-reduced-motion`.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] Each panel shows a skeleton of its chart height while loading, and no chart
- [x] The chart comes back when loading ends
- [ ] Works in light and dark themes; no animation with reduced motion
- [x] `npm run build` and `npm test` pass
