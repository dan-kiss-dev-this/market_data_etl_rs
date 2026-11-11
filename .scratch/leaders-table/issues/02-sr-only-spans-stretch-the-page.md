# 02: Screen-reader labels stretch the page below the app

**What to build:** The page scrolled about 2000px past the end of the app into empty space. The `.sr-only` spans in the leaders table (e.g. "RS line at a 52-week high", " up") are `position: absolute`. `.table-wrap` wasn't positioned, so their containing block was the page rather than the scroll box. They sat at their rows' positions in the full, unscrolled table, outside the 760px scroll box's clipping, and made the document as tall as the whole table.

Fix: `position: relative` on `.table-wrap`, so the scroll box contains and clips them.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] The document height matches the app (checked at 1009×691: 3016px before, 1017px after)
- [ ] No empty scroll space below the app at 960px and below, where `.table-wrap` is 300px tall
- [x] `npm test` passes

## Comments
