# 05: Range picker above the chart when the layout stacks

**What to build:** At 960px and below, where `.layout` stacks the table above the chart, move the chart range picker (`.segmented`) out of the filters toolbar and render it directly above the chart card. It ends up between the table and the chart it controls. Wider screens keep it in the toolbar.

CSS can't move it there because the toolbar and the chart have different parents, and `display: contents` on the toolbar would break its `role="toolbar"`. Instead, a `useMediaQuery` hook (`frontend/src/useMediaQuery.ts`, built on `useSyncExternalStore` + `matchMedia`) tells `App.tsx` which of the two places to render the picker in. The hook's `STACKED` query has to match the `.layout` breakpoint (960px) in `index.css`.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] At 960px and below (e.g. 375×667 and 768px), the range buttons sit between the table and the chart, and the toolbar shows only Sector and the legend note
- [ ] Above 960px, the range buttons are back in the toolbar
- [ ] Resizing across 960px moves the picker live, and the selected range is kept
- [x] `npm run build` passes

## Comments

At first this used the 480px phone breakpoint. It was changed to 960px so the picker moves whenever the table and chart stack.
