"""Run the SQL versions of the analyses with DuckDB (in-memory, on the cleaned tables).

    python -m bestsellers.sql                 # run every query and print the results
    python -m bestsellers.sql top_authors     # run one query
"""
from __future__ import annotations

import re
import sys

import duckdb
import pandas as pd

from .data import ROOT, load

SQL_PATH = ROOT / "sql" / "queries.sql"


def parse_queries(text: str) -> dict[str, str]:
    """Split a .sql file into {name: query} using `-- name: <id>` tags."""
    parts = re.split(r"^--\s*name:\s*(\w+)\s*$", text, flags=re.MULTILINE)
    return {name: body.strip().rstrip(";") for name, body in zip(parts[1::2], parts[2::2])}


def connect(appearances: pd.DataFrame | None = None, books: pd.DataFrame | None = None):
    if appearances is None or books is None:
        appearances, books, _ = load()
    con = duckdb.connect()
    con.register("appearances", appearances.assign(genre=appearances["genre"].astype(str)))
    con.register("books", books.assign(genre=books["genre"].astype(str)))
    return con


def run(name: str, con=None) -> pd.DataFrame:
    queries = parse_queries(SQL_PATH.read_text())
    if name not in queries:
        raise KeyError(f"Unknown query {name!r}. Available: {', '.join(queries)}")
    return (con or connect()).execute(queries[name]).df()


def main() -> None:
    con = connect()
    names = sys.argv[1:] or list(parse_queries(SQL_PATH.read_text()))
    with pd.option_context("display.width", 160, "display.max_columns", 20):
        for n in names:
            print(f"\n=== {n} ===")
            print(run(n, con).to_string(index=False))


if __name__ == "__main__":
    main()
