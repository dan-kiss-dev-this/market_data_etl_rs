# 05: An empty DATABASE_URL fails with a clear message

**What to build:** When `DATABASE_URL` is set but empty, the backend stops at startup with an error that names `DATABASE_URL`, instead of psycopg trying the local Unix socket. GitHub Actions passes an empty string for a secret the repo doesn't have, so a Daily refresh run in a repo without the secret failed with `connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed`, which hides the cause. Unset still means local Postgres (dev default).

The repo that failed is `market_data_etl_backup`. Its owner adds the `DATABASE_URL` and `MASSIVE_API_KEY` secrets there (see 02), or disables Daily refresh in that repo if it shouldn't write to production. An agent must not read, print or copy `backend/.env*`.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] Tests: unset gives the local default, set is used as is, empty or blank raises naming `DATABASE_URL`
- [x] `config.database_url(environ)` implements that and sets `DATABASE_URL`
- [x] `DATABASE_URL= python -m app.etl --rs-only` exits with the new message
- [ ] Owner: secrets added to `market_data_etl_backup`, or Daily refresh disabled there

## Comments

- Cause of the failed run: the runner path was `market_data_etl_backup`, a repo without the `DATABASE_URL` secret. Actions passed `""`, `os.environ.get` kept it (set, just empty), and libpq read an empty conninfo as the local socket.
- `DATABASE_URL= uv run --no-sync python -m app.etl --rs-only` now stops with `RuntimeError: DATABASE_URL is set but empty; ...`. Full suite: 55 passed.
- Still open: the owner adds the secrets to `market_data_etl_backup` or disables Daily refresh there.
