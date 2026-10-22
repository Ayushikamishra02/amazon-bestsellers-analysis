"""Loading, schema validation and cleaning.

The raw file has one row per (book, year) appearance on Amazon's annual Top-50 list.
Cleaning produces two tidy tables:

* ``appearances``: 550 rows, one per list slot (book x year), used for *trend* questions
* ``books``: one row per unique title, used for *book-level* questions such as
  "are fiction books rated higher?" so that evergreen titles are not counted 10 times
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = ROOT / "data" / "raw" / "bestsellers.csv"

RAW_COLUMNS = {
    "Name": "title",
    "Author": "author",
    "User Rating": "rating",
    "Reviews": "reviews",
    "Price": "price",
    "Year": "year",
    "Genre": "genre",
}

# Same person spelled two ways in the source data.
AUTHOR_FIXES = {
    "George R.R. Martin": "George R. R. Martin",
    "J.K. Rowling": "J. K. Rowling",
}


class DataValidationError(ValueError):
    """Raised when the raw file does not match the expected schema."""


@dataclass
class CleaningLog:
    """Human-readable record of every change made during cleaning."""

    steps: list[str] = field(default_factory=list)

    def add(self, msg: str) -> None:
        self.steps.append(msg)

    def __str__(self) -> str:
        return "\n".join(f"- {s}" for s in self.steps)


def load_raw(path: str | Path = RAW_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    validate_raw(df)
    return df


def validate_raw(df: pd.DataFrame) -> None:
    missing = set(RAW_COLUMNS) - set(df.columns)
    if missing:
        raise DataValidationError(f"Missing columns: {sorted(missing)}")
    if df[list(RAW_COLUMNS)].isna().any().any():
        raise DataValidationError("Unexpected missing values in raw data")
    if not df["User Rating"].between(1, 5).all():
        raise DataValidationError("Ratings must be between 1 and 5")
    if (df["Price"] < 0).any() or (df["Reviews"] < 0).any():
        raise DataValidationError("Negative price or review count")
    if not set(df["Genre"]) <= {"Fiction", "Non Fiction"}:
        raise DataValidationError(f"Unknown genres: {set(df['Genre'])}")


def _normalise_title_key(title: str) -> str:
    """Lower-case alphanumeric key used to detect titles spelled slightly differently."""
    return re.sub(r"[^a-z0-9]", "", title.lower())


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, CleaningLog]:
    """Return the tidy ``appearances`` table plus a log of what changed."""
    log = CleaningLog()
    df = raw.rename(columns=RAW_COLUMNS).copy()

    n_exact_dupes = int(df.duplicated().sum())
    log.add(f"Exact duplicate rows: {n_exact_dupes} (each row is a distinct book-year list slot, so nothing to drop)")

    for col in ("title", "author"):
        df[col] = df[col].str.strip().str.replace(r"\s+", " ", regex=True)

    n_author = int(df["author"].isin(AUTHOR_FIXES).sum())
    df["author"] = df["author"].replace(AUTHOR_FIXES)
    log.add(f"Unified {len(AUTHOR_FIXES)} author name variants affecting {n_author} rows "
            f"({', '.join(f'{k!r} -> {v!r}' for k, v in AUTHOR_FIXES.items())})")

    # Titles that differ only in punctuation/case -> keep the most frequent spelling
    df["_key"] = df["title"].map(_normalise_title_key)
    canonical = df.groupby("_key")["title"].agg(lambda s: s.value_counts().index[0])
    changed = df["title"] != df["_key"].map(canonical)
    if changed.any():
        log.add(f"Unified {int(changed.sum())} rows whose titles differed only in punctuation/case "
                f"(e.g. {df.loc[changed, 'title'].iloc[0]!r})")
    df["title"] = df["_key"].map(canonical)
    df = df.drop(columns="_key")

    df["genre"] = df["genre"].astype("category")
    df["price"] = df["price"].astype(float)
    df["is_free"] = df["price"].eq(0)
    log.add(f"Flagged {int(df['is_free'].sum())} rows with price $0 (free/promotional listings); "
            "they are excluded from price statistics but kept everywhere else")

    dup_slots = int(df.duplicated(["title", "author", "year"]).sum())
    if dup_slots:
        log.add(f"{dup_slots} title-year pairs appear twice (different editions of the same book in one year); kept as separate list slots")

    log.add("NOTE: `reviews` (and mostly `rating`) is a single 2020 snapshot repeated for every year a book "
            "appears; it is NOT a per-year measure, so review trends over time are not analysed")
    return df.sort_values(["year", "title"]).reset_index(drop=True), log


def to_books(appearances: pd.DataFrame) -> pd.DataFrame:
    """Collapse to one row per unique (title, author) with list-longevity features."""
    books = (
        appearances.groupby(["title", "author"], observed=True)
        .agg(
            genre=("genre", "first"),
            rating=("rating", "mean"),
            reviews=("reviews", "max"),
            price=("price", "median"),
            first_year=("year", "min"),
            last_year=("year", "max"),
            years_on_list=("year", "nunique"),
        )
        .reset_index()
    )
    books["genre"] = books["genre"].astype("category")
    books["is_free"] = books["price"].eq(0)
    books["evergreen"] = books["years_on_list"] >= 5
    return books


def load() -> tuple[pd.DataFrame, pd.DataFrame, CleaningLog]:
    """Convenience: raw -> (appearances, books, log)."""
    appearances, log = clean(load_raw())
    return appearances, to_books(appearances), log
