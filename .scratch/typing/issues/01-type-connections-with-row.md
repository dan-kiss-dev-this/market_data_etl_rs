# 01: Type connections with the custom Row

**What to build:** Make the psycopg type hints say what the connections really return. `CONNECT_KWARGS` installs `row_factory`, which builds `Row` objects (readable by position or column name), but every `conn` is annotated as bare `psycopg.Connection`, which type checkers read as `Connection[TupleRow]`. Pylance therefore flags name-indexed rows such as `row["fetched_at"]` in `blurbs.py`. Annotate `row_factory` as returning `RowMaker[Row]`, `connect()` and every `conn` parameter as `psycopg.Connection[Row]`, and `pool()` as `ConnectionPool[psycopg.Connection[Row]]`. No runtime behaviour changes.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] Pyright reports no `reportCallIssue`/`reportArgumentType` on name-indexed rows (e.g. `blurbs.py` `row["fetched_at"]`)
- [x] `uv run pytest` passes
