import re

from app import db

# What a migration may never do to production data; anything like this is a manual step after a backup
DESTRUCTIVE = re.compile(r"\b(DROP|TRUNCATE|DELETE)\b|\bALTER\s+COLUMN\s+\w+\s+(SET\s+DATA\s+)?TYPE\b", re.IGNORECASE)


def test_only_local_databases_count_as_local():
    assert db.is_local("postgresql://postgres@localhost:5432/market")
    assert db.is_local("postgresql://postgres@127.0.0.1/market")
    assert db.is_local("postgresql:///market")  # Unix socket
    assert not db.is_local("postgresql://postgres.ref:pw@aws-0-us-east-2.pooler.supabase.com:5432/postgres")


def test_pending_migrations_fill_gaps_in_order():
    assert db.pending(set(), 3) == [1, 2, 3]
    assert db.pending({1, 2, 3}, 3) == []
    assert db.pending({1, 3}, 4) == [2, 4]


def test_schema_gaps_name_missing_tables_and_migrations(monkeypatch):
    monkeypatch.setattr(db, "MIGRATIONS", ["ALTER TABLE companies ADD COLUMN x TEXT"])
    everything = set(db.SCHEMA_TABLES)
    assert db.schema_gaps(everything, {1}) == []
    assert db.schema_gaps(everything - {"blurbs"}, set()) == ["table blurbs", "migration 1"]


def test_every_schema_table_is_found():
    assert {"daily_bars", "blurbs", "chat_usage", "schema_migrations"} <= set(db.SCHEMA_TABLES)


def test_migrations_never_destroy_data():
    assert [m for m in db.MIGRATIONS if DESTRUCTIVE.search(m)] == []


def test_destructive_sql_is_recognised():
    assert DESTRUCTIVE.search("ALTER TABLE daily_bars DROP COLUMN volume")
    assert DESTRUCTIVE.search("truncate blurbs")
    assert DESTRUCTIVE.search("ALTER TABLE daily_bars ALTER COLUMN close TYPE NUMERIC")
    assert not DESTRUCTIVE.search("ALTER TABLE daily_bars ADD COLUMN open DOUBLE PRECISION")
    assert not DESTRUCTIVE.search("CREATE INDEX IF NOT EXISTS idx_bars_date ON daily_bars (date)")
