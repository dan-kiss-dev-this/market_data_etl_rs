from datetime import date

from app import etl

SATURDAY = date(2026, 11, 7)
TUESDAY = date(2026, 11, 10)


def test_saturday_run_ends_at_friday():
    assert etl.pending_days(SATURDAY, 7, set())[-1] == "2026-11-06"


def test_tuesday_run_ends_at_monday_and_skips_weekend():
    assert etl.pending_days(TUESDAY, 4, set()) == ["2026-11-06", "2026-11-09"]


def test_fetched_days_are_skipped():
    done = {"2026-11-03", "2026-11-05"}
    assert etl.pending_days(SATURDAY, 7, done) == ["2026-11-02", "2026-11-04", "2026-11-06"]


def test_fully_fetched_window_is_empty():
    done = set(etl.pending_days(SATURDAY, 30, set()))
    assert etl.pending_days(SATURDAY, 30, done) == []


def test_window_starts_days_before_today():
    # 2026-11-07 minus 5 days is Monday 2026-11-02; minus 6 is Sunday, so it adds nothing
    assert etl.pending_days(SATURDAY, 5, set())[0] == "2026-11-02"
    assert etl.pending_days(SATURDAY, 4, set())[0] == "2026-11-03"
    assert etl.pending_days(SATURDAY, 6, set()) == etl.pending_days(SATURDAY, 5, set())
