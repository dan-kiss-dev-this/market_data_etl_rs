# 07: The Daily refresh saves the Market direction every trading day

**What to build:** At the end of each Daily refresh, after RS Ratings are computed, save the Market direction for the latest rated date to `market_directions`. The AI Researcher panel (and chat) shows the latest Market direction with every Blurb instead of the one from the Blurb's date, and the badge shows its own date.

**Blocked by:** None

**Status:** ready-for-agent

- [x] `save_market` moves to `app/market.py`; `etl.update_market_direction` runs after `compute_rs`
- [x] `current_blurb` joins the newest `market_directions` row
- [x] The badge reads "S&P 500 on <date>: <status>"
- [x] README and spec updated
- [x] `uv run pytest` and `npx vitest run` pass

## Comments

- Before this, a row was added only by the Blurb run (by hand, about weekly), and the panel showed that date's direction, so it could be a week old.
- The Blurb text itself is still written from the Market direction on its own date; only the badge and chat context are fresher.
- Verified on local Postgres, 2026-11-13: `app.etl --rs-only` saved 2026-11-12 (Under pressure, breadth 70%), and `current_blurb` paired the 2026-11-10 Blurb with it.
