import numpy as np
import pytest

from bestsellers import analysis as A
from bestsellers.data import load
from bestsellers.sql import connect, parse_queries, run


@pytest.fixture(scope="module")
def data():
    appearances, books, _ = load()
    return appearances, books


def test_genre_share_rows_sum_to_one(data):
    share = A.genre_share_by_year(data[0])
    np.testing.assert_allclose(share.sum(axis=1), 1.0, atol=1e-3)
    assert list(share.index) == list(range(2009, 2020))


def test_rating_summary_counts_each_book_once(data):
    _, books = data
    assert A.rating_summary_by_genre(books)["books"].sum() == len(books)


def test_compare_genres_returns_valid_stats(data):
    _, books = data
    res = A.compare_genres(books, "rating")
    assert 0 <= res["p_value"] <= 1
    assert -1 <= res["rank_biserial"] <= 1
    assert res["n_fiction"] + res["n_nonfiction"] == len(books)


def test_price_stats_exclude_free_books(data):
    _, books = data
    res = A.compare_genres(books, "price", exclude_free=True)
    assert res["n_fiction"] + res["n_nonfiction"] == (~books["is_free"]).sum()


def test_top_authors_distinguishes_appearances_from_titles(data):
    t = A.top_authors(data[0], 10)
    assert (t["list_appearances"] >= t["unique_titles"]).all()
    assert t.loc["Gary Chapman", "unique_titles"] == 2
    assert t.loc["Jeff Kinney", "list_appearances"] == 12


def test_headline_numbers(data):
    h = A.headline(*data)
    assert h["list_slots"] == 550
    assert h["unique_books"] == 350
    assert 0 < h["share_books_one_year"] < 1


def test_price_outliers_are_above_fence(data):
    _, books = data
    out = A.price_outliers(books)
    assert out["price"].min() > books.loc[~books["is_free"], "price"].median()
    assert out.iloc[0]["price"] == 105


# ---------------------------------------------------------------- SQL parity
@pytest.fixture(scope="module")
def con(data):
    return connect(*data)


def test_sql_file_parses():
    from bestsellers.sql import SQL_PATH
    queries = parse_queries(SQL_PATH.read_text())
    assert {"genre_share_by_year", "top_authors", "rating_by_genre", "evergreens"} <= set(queries)


def test_sql_matches_pandas_genre_share(con, data):
    sql = run("genre_share_by_year", con).set_index("year")["fiction_share"]
    pd_share = A.genre_share_by_year(data[0])["Fiction"]
    np.testing.assert_allclose(sql.values, pd_share.values, atol=1e-3)


def test_sql_matches_pandas_top_authors(con, data):
    sql = run("top_authors", con).set_index("author")
    pdt = A.top_authors(data[0], 10)
    assert list(sql["list_appearances"]) == list(pdt["list_appearances"])
    assert sql.loc["Gary Chapman", "unique_titles"] == pdt.loc["Gary Chapman", "unique_titles"]


def test_sql_matches_pandas_rating_by_genre(con, data):
    sql = run("rating_by_genre", con).set_index("genre")["mean_rating"]
    pdr = A.rating_summary_by_genre(data[1])["mean"]
    pdr.index = pdr.index.astype(str)
    np.testing.assert_allclose(sql.sort_index().values, pdr.sort_index().values, atol=1e-3)


def test_unknown_query_raises(con):
    with pytest.raises(KeyError):
        run("does_not_exist", con)
