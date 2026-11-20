from datetime import date
from pathlib import Path

from evals.run_log import log_path

pytest_plugins = ["pytester"]


def test_the_log_is_named_by_the_day_it_ran():
    assert log_path(Path("x"), date(2026, 11, 20)) == Path("x/last_run_2026-11-20.txt")


def test_the_log_holds_the_console_output(pytester):
    log = pytester.path / "runs" / "last_run.txt"
    pytester.makeconftest(f"""
        import pytest
        from evals.run_log import tee_terminal

        @pytest.hookimpl(trylast=True)
        def pytest_configure(config):
            config._log = tee_terminal(config, {str(log)!r})

        def pytest_unconfigure(config):
            config._log.close()
    """)
    pytester.makepyfile("""
        def test_good():
            assert True

        def test_bad():
            assert 1 == 2, "price missing"
    """)
    pytester.runpytest("-v")
    text = log.read_text()
    assert "test_good PASSED" in text
    assert "test_bad FAILED" in text
    assert "price missing" in text
    assert "1 failed, 1 passed" in text
