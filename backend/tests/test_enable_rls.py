from app import enable_rls


def test_only_tables_without_rls_are_changed():
    rows = [("rs_ratings", False), ("blurbs", True), ("daily_bars", False)]
    assert enable_rls.missing_rls(rows) == ["daily_bars", "rs_ratings"]


def test_statements_enable_rls_without_forcing_it():
    # FORCE would make RLS apply to the owner too, locking out the backend and the Daily refresh
    statements = [s.as_string() for s in enable_rls.statements(["daily_bars", "My Table"])]
    assert statements == [
        'ALTER TABLE "daily_bars" ENABLE ROW LEVEL SECURITY',
        'ALTER TABLE "My Table" ENABLE ROW LEVEL SECURITY',
    ]
