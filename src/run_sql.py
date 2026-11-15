"""Run the DuckDB SQL files in order and export every table named out_* to data/output/<name>.csv.

Run: python src/run_sql.py
"""
from __future__ import annotations

import duckdb

from config import OUT, SIM, SQL


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    for f in sorted(SQL.glob("*.sql")):
        con.execute(f.read_text(encoding="utf-8").replace("{SIM}", SIM.as_posix()))
        print("ran", f.name)
    bad = con.execute("SELECT * FROM out_dq_checks WHERE n > 0").fetchall()
    print("data-quality checks:", "all pass" if not bad else bad)
    tables = [r[0] for r in con.execute("SELECT table_name FROM information_schema.tables "
                                        "WHERE table_name LIKE 'out_%' ORDER BY 1").fetchall()]
    for t in tables:
        con.execute(f"COPY {t} TO '{(OUT / (t[4:] + '.csv')).as_posix()}' (HEADER)")
        print(f"  {t[4:]:<22} {con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]:>7,} rows")


if __name__ == "__main__":
    main()
