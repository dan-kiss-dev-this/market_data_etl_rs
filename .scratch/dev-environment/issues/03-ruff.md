# Lint and format the backend with ruff

Status: ready-for-agent

The backend had no linter or formatter. Add ruff as a dev dependency, configured in `backend/pyproject.toml` with a 120-character line length (which matches the existing code) and import sorting (`I`) on top of ruff's default rules. Format the whole backend once, fix what `ruff check` finds, and run both in CI before pytest.

No new test: this is tooling, and CI running `ruff check` and `ruff format --check` is the check.

## Acceptance

- [x] `ruff` is in the `dev` dependency group, with `[tool.ruff]` settings in `pyproject.toml`
- [x] `uv run ruff check .` and `uv run ruff format --check .` pass in `backend/`
- [x] The `pytest` job in `.github/workflows/test.yml` runs both before pytest
- [x] README says how to run it

## Comments

- The first format run changed 15 files, mostly quote style inside f-strings. Fixed two findings: nested `with` in `pull_prod.copy` (SIM117) and `zip(x, x[1:])` → `pairwise` in `market.failed_crossings` (RUF007). pytest 86/86, 2026-11-24.
