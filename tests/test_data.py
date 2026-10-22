import pandas as pd
import pytest

from bestsellers.data import DataValidationError, clean, load_raw, to_books, validate_raw


@pytest.fixture(scope="module")
def raw():
    return load_raw()


@pytest.fixture(scope="module")
def tables(raw):
    appearances, log = clean(raw)
    return appearances, to_books(appearances), log


def test_raw_shape(raw):
    assert raw.shape == (550, 7)
    assert raw.groupby("Year").size().eq(50).all(), "every year should have 50 list slots"


def test_validation_rejects_bad_rating(raw):
    bad = raw.copy()
    bad.loc[0, "User Rating"] = 7
    with pytest.raises(DataValidationError):
        validate_raw(bad)


def test_validation_rejects_missing_column(raw):
    with pytest.raises(DataValidationError):
        validate_raw(raw.drop(columns="Genre"))


def test_author_variants_unified(tables):
    appearances, _, _ = tables
    authors = set(appearances["author"])
    assert "J.K. Rowling" not in authors and "J. K. Rowling" in authors
    assert "George R.R. Martin" not in authors


def test_title_variants_unified(tables):
    appearances, _, _ = tables
    love = appearances[appearances["title"].str.startswith("The 5 Love Languages")]["title"].unique()
    assert len(love) == 1


def test_clean_keeps_every_list_slot(tables, raw):
    appearances, _, _ = tables
    assert len(appearances) == len(raw)


def test_free_books_flagged(tables):
    appearances, _, _ = tables
    assert appearances["is_free"].sum() == (appearances["price"] == 0).sum() == 12


def test_books_table_is_one_row_per_title(tables):
    appearances, books, _ = tables
    assert not books.duplicated(["title", "author"]).any()
    assert books["years_on_list"].between(1, 11).all()
    # every list slot is accounted for by some book
    assert books["years_on_list"].sum() <= len(appearances)


def test_cleaning_log_mentions_snapshot_caveat(tables):
    *_, log = tables
    assert any("snapshot" in s for s in log.steps)


def test_clean_on_tiny_frame():
    df = pd.DataFrame({
        "Name": [" Book A ", "Book A"], "Author": ["J.K. Rowling", "J. K. Rowling"],
        "User Rating": [4.5, 4.5], "Reviews": [10, 10], "Price": [0, 10], "Year": [2010, 2011],
        "Genre": ["Fiction", "Fiction"],
    })
    appearances, _ = clean(df)
    books = to_books(appearances)
    assert len(books) == 1
    assert books.iloc[0]["years_on_list"] == 2
