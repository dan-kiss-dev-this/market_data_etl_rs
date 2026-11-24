# Market condition: Strong, Normal and Shaky market

Status: ready-for-agent

Rename the Market direction to the **Market condition**, with plainer labels and a new rule. Uptrend becomes Strong market, Under pressure becomes Normal market, and Downtrend becomes Shaky market. The `market_directions` table and the `market` JSON field keep their names.

The rule, from SPY closes in `daily_bars`, checked in this order:

1. **Shaky market** if any of these holds:
   - the close is below the 200-day average
   - the close is below the 50-day average and the 50-day is not rising (compared with 10 trading days ago)
   - the close is below the 50-day average, with at least 2 failed 50-day crossings in the last 20 trading days. A failed crossing is a close above the 50-day followed by a close back below it.
2. **Strong market** if the close is above the 50-day, the 50-day is above the 200-day, the 50-day is rising (vs 10 trading days ago) and the 200-day is rising (vs 20 trading days ago).
3. **Normal market** otherwise.

The rule needs 220 SPY bars, up from 200. Each saved row also stores `ma200_rising` and `failed_50_day_crossings`, which go into the Blurb and chat prompts but not onto the badge. Distribution days were considered and left out.

The definition at the bottom of the Blurb uses the owner's wording:

- Strong market: "Above rising 50- and 200-day averages, with the 50-day above the 200-day. Pullbacks are shallow and bought fast, and it makes new highs after confirming rallies."
- Normal market: "Above the 200-day and mostly above the 50-day, but advancing unevenly. Pullbacks happen, and some breakouts work while others fail."
- Shaky market: "Below the 200-day, or below a falling 50-day average, or repeatedly failing at it. Rallies fade quickly and breakdowns hit new lows."

## Backfill

The rows already stored in `market_directions` hold the old labels. After deploying, run this once against Supabase:

```
cd backend && uv run --env-file .env.production python -m app.market --backfill
```

It recomputes every stored date from `daily_bars` with the new rule, and deletes rows whose date has fewer than 220 SPY bars before it. Then do a Blurb run (`uv run --env-file .env.production python -m app.blurbs`), so that Blurbs that mention the old labels are rewritten.

## Acceptance

- [x] Tests first: `test_market.py` covers each branch of the rule, the 220-bar minimum, the two new fields and the backfill. `test_blurbs.py`, `test_chat_with_ai.py` and `AiResearcher.test.tsx` check the new labels and text.
- [x] `market.py` uses the new rule and has `--backfill`
- [x] The Blurb and chat prompts describe the 200-day slope and failed crossings
- [x] The panel shows the new labels and definitions
- [x] `GLOSSARY.md` has Market condition, Strong market, Normal market and Shaky market
- [x] Spec updated, including the backfill and Blurb run steps
- [x] README and `docs/todo-ideas.md` say Market condition

## Comments
- pytest 86/86, vitest 48/48, tsc clean, 2026-11-24. The backfill and Blurb run against Supabase are still to do after deploy.
