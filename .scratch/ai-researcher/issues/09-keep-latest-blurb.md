# Keep showing the latest Blurb, however old

Status: ready-for-agent

The panel stopped showing a Blurb once it was more than 7 days old, so all 50 vanished on 2026-11-18 when no new Blurb run had happened. The Blurbs were still in the `blurbs` table. Instead, `current_blurb` returns the ticker's latest Blurb whatever its age, until a new Blurb run replaces it. The panel already shows "Updated {date}", so the age stays visible. A company that drops out of the top 50 keeps its last Blurb.

## Acceptance

- [x] A test in `test_blurbs.py` checks that `current_blurb` returns a Blurb dated long before today, and a Vitest test checks the new "No Blurb yet" copy
- [x] `current_blurb` has no age check; `is_current` and `BLURB_MAX_AGE_DAYS` are gone
- [x] The panel says "No Blurb yet. Blurbs cover the top 50 by RS rating." when there's none
- [x] Spec and README updated

## Comments

- pytest 81/81, vitest 46/46 passing, 2026-11-20.
