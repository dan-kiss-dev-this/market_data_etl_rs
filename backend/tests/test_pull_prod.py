from app import pull_prod


def test_only_local_databases_can_be_written():
    assert pull_prod.is_local("postgresql://postgres@localhost:5432/market")
    assert pull_prod.is_local("postgresql://postgres@127.0.0.1/market")
    assert pull_prod.is_local("postgresql:///market")  # Unix socket
    assert not pull_prod.is_local("postgresql://postgres.ref:pw@aws-0-us-east-2.pooler.supabase.com:5432/postgres")


def test_tickers_whose_history_differs_are_recopied():
    local = {"AAPL": (500, 90000.0), "NVDA": (500, 50000.0), "OLD": (300, 1000.0)}
    remote = {
        "AAPL": (500, 90000.0 + 1e-8),  # float noise from summing in another order
        "NVDA": (500, 5000.0),  # 10-for-1 split adjusted the old closes
        "NEW": (480, 2000.0),  # added to the S&P 500 with its history
    }
    assert pull_prod.changed_tickers(local, remote) == ["NEW", "NVDA", "OLD"]
