# 04: AI Researcher panel shows the Blurb

**What to build:** `GET /api/rs/{ticker}/blurb`, plus the AI Researcher panel showing the Blurb with a Market direction badge, its date and up to 3 cited headline links. See `../spec.md`.

**Blocked by:** 03

**Status:** ready-for-agent

- [x] The endpoint returns the latest Blurb if it is at most 7 days old, with that date's Market direction. Otherwise it returns 404
- [x] The panel shows "Looking up {name}…" while loading, then the badge, the five fields, "Updated {date}" and the source links
- [x] On 404 the panel shows "No current Blurb. Blurbs cover the top 50 by RS rating."
- [ ] Works in light and dark themes and at phone width
- [x] `uv run pytest`, `npm test` and `npm run build` pass

## Comments

- Network or server errors show "Couldn't load the Blurb right now. Try again later." so they don't look like "No current Blurb".
- If the endpoint runs against a database that has never had a Blurb run, the tables don't exist yet; it returns 404 rather than 500.
- Open: checking it in the browser in light and dark themes and at phone width, once real Blurbs exist.
