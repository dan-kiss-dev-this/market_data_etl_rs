# 01: Evals run with pytest

**What to build:** The live high-close eval becomes a pytest suite under `backend/evals/`, one parametrized test per case, run by hand with `uv run pytest evals`. A plain `uv run pytest` (and CI) still runs only `tests/`, so it never calls Haiku. The cases and the grader (`check`) move to `evals/high_close.py` and get offline unit tests in `tests/`, so a broken grader shows up in CI.

**Blocked by:** None

**Status:** ready-for-agent

- [x] Tests first: `tests/test_evals.py` checks the grader: a correct reply passes; a wrong ticker, a missing price, date or 2-year caveat, an extra tool call, a call on an unrelated question, and a price quoted with no stored row each fail
- [x] `evals/high_close.py` holds `Case`, `CASES` and the grader; `evals/conftest.py` gives `conn` and `ai` fixtures; `evals/test_high_close_eval.py` records tool calls with `monkeypatch` and asserts the grader passes
- [x] `testpaths = ["tests"]` in `pyproject.toml`; `evals/high_close_eval.py` removed
- [x] README updated with the new run command
- [x] `uv run pytest` passes without running the eval; `uv run pytest evals` passes 6/6

## Comments

- Verified 2026-11-16: `uv run pytest` runs 78 tests and collects nothing from `evals/`; `uv run pytest evals` passed 6/6 against live Haiku and local Postgres.
