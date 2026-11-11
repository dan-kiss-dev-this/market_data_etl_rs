# 01: AI Researcher button with a placeholder panel

**What to build:** A floating "AI Researcher" button fixed at the bottom middle of the viewport, shown once a company is selected. Clicking it opens a panel above the button that names the company being researched (name and ticker of the selected company) and says "Service Not Available". Clicking the button again closes the panel. The button reports `aria-expanded`, and the panel follows the selection if the user picks another company while it is open. There is no backend call yet; this is a placeholder for a future research service.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] The button floats at the bottom middle of the viewport and stays put while the page scrolls
- [x] Clicking it shows the selected company's name and ticker and "Service Not Available"
- [x] Clicking it again hides the panel
- [ ] Works in light and dark themes and at phone width
- [x] `npm run build` and `npm test` pass

## Comments

- Moved from the chart card header to a floating button at the bottom middle of the viewport, at the user's request. The page gets extra bottom padding so the button doesn't cover the end of the table.
