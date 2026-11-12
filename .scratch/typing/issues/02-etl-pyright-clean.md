# 02: Clear Pyright errors in etl.py

**What to build:** Aggregate queries (`MIN`, `MAX`, `COUNT`) always return one row, but `.fetchone()` is typed `Row | None`. Add `one(cursor)` to `db.py`, which returns the row or raises `LookupError`, and use it for every `.fetchone()` in `etl.py`. Change `rs.compute_ratings`'s `closes_by_ticker` from `dict` to `Mapping`, since it only reads it.

**Blocked by:** 01

**Status:** ready-for-agent

- [x] Pyright reports no errors in `etl.py`
- [x] `uv run pytest` passes
- [x] `history_window` and `print_summary` give the same output against the real database
