"""Evals run live against real Haiku and DATABASE_URL, so they are not in CI (a full run costs about 1¢).
Run them by hand from backend/: uv run pytest evals
Each run's console output is saved to evals/runs/last_run_<date>.txt (see evals/run_log.py)."""

from datetime import date
from pathlib import Path
from typing import TextIO

import pytest

from app import chat_with_ai
from app.db import connect
from evals.run_log import log_path, tee_terminal

RUN_LOG = pytest.StashKey[TextIO]()


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    config.stash[RUN_LOG] = tee_terminal(config, log_path(Path(__file__).parent / "runs", date.today()))


def pytest_unconfigure(config):
    config.stash[RUN_LOG].close()


@pytest.fixture(scope="session")
def conn():
    conn = connect()
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def ai():
    return chat_with_ai.ai_client()
