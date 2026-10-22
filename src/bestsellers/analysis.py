"""Analytical questions, each answered by one small, testable function.

Convention: functions taking ``appearances`` answer *list-slot / trend* questions;
functions taking ``books`` answer *per-book* questions (each title counted once).
"""
from __future__ import annotations

import pandas as pd
from scipy import stats


# ----------------------------------------------------------------------------
# Q1. Genre mix over time
# ----------------------------------------------------------------------------
def genre_share_by_year(appearances: pd.DataFrame) -> pd.DataFrame:
    t = pd.crosstab(appearances["year"], appearances["genre"], normalize="index")
    return t.rename(columns=str).round(3)


def genre_trend_test(appearances: pd.DataFrame) -> dict:
    """Is the fiction share trending over the decade? (OLS on yearly share)."""
    share = genre_share_by_year(appearances)["Fiction"]
    res = stats.linregress(share.index, share.values)
    return {
        "fiction_share_overall": float((appearances["genre"] == "Fiction").mean()),
        "slope_per_year": float(res.slope),
        "p_value": float(res.pvalue),
        "min_year": int(share.idxmin()), "min_share": float(share.min()),
        "max_year": int(share.idxmax()), "max_share": float(share.max()),
    }


# ----------------------------------------------------------------------------
# Q2. Ratings
# ----------------------------------------------------------------------------
def rating_summary_by_genre(books: pd.DataFrame) -> pd.DataFrame:
    """Per-book rating stats by genre (the corrected version of v1's avg_rating_by_genre)."""
    return (books.groupby("genre", observed=True)["rating"]
            .agg(books="size", mean="mean", median="median", std="std", min="min", max="max")
            .round(3))


def compare_genres(books: pd.DataFrame, column: str, exclude_free: bool = False) -> dict:
    """Mann-Whitney U test (ratings & prices are skewed / bounded, so no t-test)."""
    b = books[~books["is_free"]] if exclude_free else books
    fic = b.loc[b["genre"] == "Fiction", column]
    non = b.loc[b["genre"] == "Non Fiction", column]
    u, p = stats.mannwhitneyu(fic, non, alternative="two-sided")
    # rank-biserial correlation as effect size (-1..1)
    effect = 1 - 2 * u / (len(fic) * len(non))
    return {
        "column": column,
        "fiction_median": float(fic.median()), "nonfiction_median": float(non.median()),
        "fiction_mean": float(fic.mean()), "nonfiction_mean": float(non.mean()),
        "n_fiction": int(len(fic)), "n_nonfiction": int(len(non)),
        "u_statistic": float(u), "p_value": float(p), "rank_biserial": float(effect),
    }


def rating_by_year(appearances: pd.DataFrame) -> pd.DataFrame:
    return (appearances.groupby("year")["rating"].agg(mean="mean", median="median",
                                                      share_4_8_plus=lambda s: (s >= 4.8).mean())
            .round(3))


def rating_trend_test(appearances: pd.DataFrame) -> dict:
    rho, p = stats.spearmanr(appearances["year"], appearances["rating"])
    by_year = rating_by_year(appearances)["mean"]
    return {"spearman_rho": float(rho), "p_value": float(p),
            "mean_first_year": float(by_year.iloc[0]), "mean_last_year": float(by_year.iloc[-1])}


# ----------------------------------------------------------------------------
# Q3. Prices
# ----------------------------------------------------------------------------
def price_by_year(appearances: pd.DataFrame) -> pd.DataFrame:
    paid = appearances[~appearances["is_free"]]
    return (paid.groupby(["year", "genre"], observed=True)["price"].median()
            .unstack().rename(columns=str))


def price_trend_test(appearances: pd.DataFrame) -> dict:
    paid = appearances[~appearances["is_free"]]
    rho, p = stats.spearmanr(paid["year"], paid["price"])
    med = paid.groupby("year")["price"].median()
    return {"spearman_rho": float(rho), "p_value": float(p),
            "median_first_year": float(med.iloc[0]), "median_last_year": float(med.iloc[-1])}


def price_outliers(books: pd.DataFrame, k: float = 1.5) -> pd.DataFrame:
    """Tukey-fence outliers among paid books."""
    paid = books[~books["is_free"]]
    q1, q3 = paid["price"].quantile([0.25, 0.75])
    upper = q3 + k * (q3 - q1)
    return (paid[paid["price"] > upper]
            .sort_values("price", ascending=False)[["title", "author", "genre", "price"]]
            .reset_index(drop=True))


# ----------------------------------------------------------------------------
# Q4. Popularity (reviews) and relationships
# ----------------------------------------------------------------------------
def correlations(books: pd.DataFrame) -> pd.DataFrame:
    cols = ["rating", "reviews", "price", "years_on_list"]
    return books.loc[~books["is_free"], cols].corr(method="spearman").round(3)


def most_reviewed(books: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    return (books.nlargest(n, "reviews")[["title", "author", "genre", "reviews", "rating", "years_on_list"]]
            .reset_index(drop=True))


# ----------------------------------------------------------------------------
# Q5. Authors
# ----------------------------------------------------------------------------
def top_authors(appearances: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Corrected version of v1's author_counts: v1 counted *list appearances*
    and called them 'books published'. We report both."""
    t = (appearances.groupby("author")
         .agg(list_appearances=("title", "size"), unique_titles=("title", "nunique"),
              years_active=("year", "nunique"), genre=("genre", lambda s: s.mode().iat[0]),
              avg_rating=("rating", "mean"))
         .sort_values(["list_appearances", "unique_titles"], ascending=False)
         .head(n))
    t["avg_rating"] = t["avg_rating"].round(2)
    t["genre"] = t["genre"].astype(str)
    return t


def author_concentration(appearances: pd.DataFrame, top: int = 10) -> dict:
    counts = appearances["author"].value_counts()
    return {
        "unique_authors": int(counts.size),
        f"top_{top}_share_of_slots": float(counts.head(top).sum() / counts.sum()),
        "one_appearance_authors_share": float((counts == 1).mean()),
    }


# ----------------------------------------------------------------------------
# Q6. Longevity
# ----------------------------------------------------------------------------
def evergreens(books: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    return (books.sort_values(["years_on_list", "reviews"], ascending=False)
            .head(n)[["title", "author", "genre", "years_on_list", "first_year", "last_year", "rating"]]
            .reset_index(drop=True))


def longevity_distribution(books: pd.DataFrame) -> pd.Series:
    return books["years_on_list"].value_counts().sort_index()


def longevity_by_genre(books: pd.DataFrame) -> pd.DataFrame:
    return (books.groupby("genre", observed=True)
            .agg(books=("title", "size"), mean_years=("years_on_list", "mean"),
                 share_one_year=("years_on_list", lambda s: (s == 1).mean()),
                 share_evergreen=("evergreen", "mean"))
            .round(3))


# ----------------------------------------------------------------------------
# Headline numbers used by the README / report
# ----------------------------------------------------------------------------
def headline(appearances: pd.DataFrame, books: pd.DataFrame) -> dict:
    return {
        "list_slots": int(len(appearances)),
        "unique_books": int(len(books)),
        "unique_authors": int(appearances["author"].nunique()),
        "years": f"{appearances['year'].min()}-{appearances['year'].max()}",
        "share_rated_4_5_plus": float((books["rating"] >= 4.5).mean()),
        "share_books_one_year": float((books["years_on_list"] == 1).mean()),
        "free_rows": int(appearances["is_free"].sum()),
    }
