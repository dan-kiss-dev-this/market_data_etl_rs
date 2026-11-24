"""Turn on Row-Level Security for every table in public that doesn't have it yet.

Run from backend/:  uv run --env-file .env.production python -m app.enable_rls   (Supabase)
                    uv run python -m app.enable_rls                              (local Postgres)
Supabase serves every public table on its REST API to anyone with the project's public anon key. RLS with no
policies shuts that API out. The backend, the Daily refresh and pull_prod connect as the tables' owner, which
RLS doesn't apply to, so they're unaffected. Never FORCE it: that would lock them out too. Safe to rerun;
run it after adding a table (ALTER TABLE keeps RLS on).
"""

from collections.abc import Iterable

from psycopg import sql

from app.db import connect

TABLES = "SELECT relname, relrowsecurity FROM pg_class WHERE relnamespace = 'public'::regnamespace AND relkind = 'r'"


def missing_rls(rows: Iterable[tuple[str, bool]]) -> list[str]:
    return sorted(name for name, rls in rows if not rls)


def statements(names: list[str]) -> list[sql.Composed]:
    return [sql.SQL("ALTER TABLE {} ENABLE ROW LEVEL SECURITY").format(sql.Identifier(n)) for n in names]


def main() -> None:
    conn = connect()
    rows = conn.execute(TABLES).fetchall()
    names = missing_rls(rows)
    with conn.transaction():
        for statement in statements(names):
            conn.execute(statement)
    for name in names:
        print(f"RLS on: {name}")
    print(f"RLS already on for all {len(rows)} tables" if not names else f"{len(names)} of {len(rows)} tables changed")


if __name__ == "__main__":
    main()
