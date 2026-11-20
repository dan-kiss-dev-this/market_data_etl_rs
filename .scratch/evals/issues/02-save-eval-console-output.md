# 02: Save each eval run's console output

**What to build:** Every `uv run pytest evals` run also writes its full console output to `backend/evals/runs/last_run_<YYYY-MM-DD>.txt`. A second run on the same day overwrites that day's file. The logs are committed, not ignored: the evals call live Haiku, so no run can be repeated, and the log is the only record of how the model behaved that day. A plain `uv run pytest` (and CI) writes no log.

**Blocked by:** 01

**Status:** ready-for-agent

- [x] Tests first: `tests/test_run_log.py` checks that `log_path` names the file by date, and (with `pytester`) that `tee_terminal` writes the PASSED/FAILED lines, the assertion message and the summary line to the file
- [x] `evals/run_log.py` holds `log_path` and `tee_terminal`, which copies terminal writes the way pytest's `pastebin` plugin does
- [x] `evals/conftest.py` starts the tee in `pytest_configure` and closes the file in `pytest_unconfigure`
- [x] README and the `evals/conftest.py` docstring say where the log goes
- [x] `uv run pytest` passes and writes no log; `uv run pytest evals` writes a log that matches the terminal

## Comments

- 2026-11-20: `uv run pytest` runs 80 tests and writes no log. `uv run pytest evals --collect-only` wrote `evals/runs/last_run_2026-11-20.txt`, matching the terminal. A live `uv run pytest evals -v` passed 6/6, and its log matches the terminal.
