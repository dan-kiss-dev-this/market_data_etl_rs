import pytest

from app import config


def test_unset_database_url_means_local_postgres():
    assert config.database_url({}) == "postgresql://postgres@localhost:5432/market"


def test_set_database_url_is_used():
    url = "postgresql://postgres.ref:pw@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
    assert config.database_url({"DATABASE_URL": url}) == url


@pytest.mark.parametrize("value", ["", "  "])
def test_empty_database_url_is_an_error(value):
    # GitHub Actions passes "" for a secret the repo doesn't have
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        config.database_url({"DATABASE_URL": value})
