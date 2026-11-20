"""Saves an eval run's console output to a dated file, since a live run can't be repeated. The logs in
evals/runs/ are committed as the history of how the model did."""

from datetime import date
from pathlib import Path
from typing import TextIO

import pytest


def log_path(runs_dir: Path, day: date) -> Path:
    return runs_dir / f"last_run_{day.isoformat()}.txt"


def tee_terminal(config: pytest.Config, path: Path | str) -> TextIO:
    """Copy everything pytest prints into the file at path, as pytest's own pastebin plugin does.
    The caller closes the returned file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    log = path.open("w")
    tw = config.pluginmanager.getplugin("terminalreporter")._tw
    write = tw.write

    def tee(s: str, **kwargs) -> None:
        write(s, **kwargs)
        log.write(s)

    tw.write = tee
    return log
