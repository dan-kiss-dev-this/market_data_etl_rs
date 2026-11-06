"""Copy every table from the old SQLite file into Postgres (DATABASE_URL).

Run from backend/:  uv run python -m app.migrate_sqlite [path/to/market.db]
The SQLite file is opened read-only. Safe to re-run: target tables are emptied first.
"""

import sqlite3
import sys
from pathlib import Path

from app.config import SQLITE_PATH
from app.db import connect, init_schema

TABLES = ("companies", "daily_bars", "fetched_dates", "splits_applied", "history_checked", "rs_ratings")
BOOL_COLUMNS = {"rs_ratings": {"rs_new_high"}}  # stored as 0/1 in SQLite


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else SQLITE_PATH
    src = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    dst = connect()
    init_schema(dst)

    counts = {}
    with dst.transaction():
        dst.execute(f"TRUNCATE {', '.join(TABLES)}")
        for table in TABLES:
            cur = src.execute(f"SELECT * FROM {table}")
            columns = [c[0] for c in cur.description]
            bools = [i for i, c in enumerate(columns) if c in BOOL_COLUMNS.get(table, ())]
            n = 0
            with dst.cursor().copy(f"COPY {table} ({', '.join(columns)}) FROM STDIN") as copy:
                for row in cur:
                    row = list(row)
                    for i in bools:
                        row[i] = bool(row[i])
                    copy.write_row(row)
                    n += 1
            counts[table] = n

    ok = True
    for table in TABLES:
        target = dst.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        match = target == counts[table]
        ok &= match
        print(f"{table:16} sqlite {counts[table]:>8,}  postgres {target:>8,}  {'ok' if match else 'MISMATCH'}")
    src.close()
    dst.close()
    if not ok:
        sys.exit("Row counts differ")


if __name__ == "__main__":
    main()
