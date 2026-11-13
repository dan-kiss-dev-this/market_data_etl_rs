from app import pull_prod


def test_tickers_whose_history_differs_are_recopied():
    local = {"AAPL": (500, 90000.0), "NVDA": (500, 50000.0), "OLD": (300, 1000.0)}
    remote = {
        "AAPL": (500, 90000.0 + 1e-8),  # float noise from summing in another order
        "NVDA": (500, 5000.0),  # 10-for-1 split adjusted the old closes
        "NEW": (480, 2000.0),  # added to the S&P 500 with its history
    }
    assert pull_prod.changed_tickers(local, remote) == ["NEW", "NVDA", "OLD"]


LOCAL = {
    "companies": ["ticker", "name", "sector", "industry"],  # a column not deployed yet
    "daily_bars": ["ticker", "date", "close", "volume"],
    "chat_usage": ["day", "visitor", "messages"],
    "watchlist": ["ticker"],  # a table not deployed yet
}
REMOTE = {
    "companies": ["ticker", "name", "sector"],
    "daily_bars": ["ticker", "date", "close", "volume"],
    "chat_usage": ["day", "visitor", "messages"],
}


def test_every_shared_table_is_replaced_except_skipped_ones():
    assert pull_prod.tables_to_replace(LOCAL, REMOTE) == ["companies"]


def test_only_columns_both_sides_have_are_copied():
    assert pull_prod.shared_columns(LOCAL, REMOTE, "companies") == "ticker, name, sector"


def test_schema_drift_is_reported():
    assert pull_prod.differences(LOCAL, REMOTE) == [
        "table watchlist: only local (not deployed yet?), not copied",
        "companies.industry: only local, left empty",
    ]
    assert pull_prod.differences(LOCAL, LOCAL) == []
