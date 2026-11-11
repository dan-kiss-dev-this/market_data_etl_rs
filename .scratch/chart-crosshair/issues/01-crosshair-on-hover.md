# 01: Crosshair on chart hover

**What to build:** When hovering a chart panel in `RsChart.tsx`, draw a horizontal line at the mouse position across the plot area, completing a crosshair with the existing vertical tooltip cursor. A small pill over the y-axis shows the value under the mouse, formatted like that panel's ticks. Only the hovered panel gets the horizontal line; the vertical line stays synced across panels via `syncId`.

The mouse y comes from a wrapper `div` around `ResponsiveContainer`. A `Crosshair` child of `LineChart` uses Recharts' `usePlotArea` and `useYAxisInverseScale` hooks (3.8+) to clip the line to the plot area and turn the pixel back into a value.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Hovering a panel shows a horizontal line at the mouse y, spanning the plot area
- [ ] The y-axis pill shows the value at the mouse, in the panel's format
- [ ] Nothing is drawn when the mouse is outside the plot area or leaves the chart
- [x] `npm run build` and `npm test` pass

## Comments

The line was later changed to solid `#ffffff` at 1px, and the vertical Tooltip cursor to match.

`Crosshair` is exported and covered by `frontend/src/components/RsChart.test.tsx`: line position, colour and width, the pill value, and drawing nothing off the plot area. An end-to-end test hovers the RS Rating panel of a full `RsChart` and checks that only that panel gets the crosshair, with the right value, and that leaving removes it. jsdom has no layout, so the tests stub `ResizeObserver` and `getBoundingClientRect` to let `ResponsiveContainer` render.
