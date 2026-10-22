# What changed from v1 ("Panda Project") and why

v1 was a single exported Jupyter script (`Bestselling amazon books with pandas.py`) that loaded the CSV,
printed summaries, cleaned a little and exported two CSVs. v2 keeps the same dataset and the same core questions,
and fixes the analysis and turns it into a reproducible project.

## Correctness fixes

| v1 code | Problem | v2 |
|---|---|---|
| `df.drop_duplicates(inplace=True)` | Removes **0 rows**: every row is a different book-year. It looked like cleaning but did nothing, and hid the real duplication problem (one book counted once per year) | Explicit `appearances` vs `books` tables; cleaning log reports what really changed |
| `df['Author'].value_counts()` commented as *"number of books published by the same author"* | Counts **list appearances**, not books. Gary Chapman: 11 appearances, 2 books | `top_authors()` reports `list_appearances` **and** `unique_titles` |
| `df.groupby("Genre")["Rating"].mean()` on raw rows | Evergreen books counted up to 10×. Fiction lead looked like 0.053 stars; per book it is 0.013 | Per-book averages + median + a significance test |
| No handling of author variants | "J.K. Rowling" and "J. K. Rowling" split into two authors | `AUTHOR_FIXES` mapping, unit-tested |
| `df["Price"].astype(float)` | Fine, but 12 $0 rows silently lowered price averages | `is_free` flag, excluded from price stats |
| `pd.read_csv('bestsellers.csv')` with no checks | A malformed file would produce wrong numbers silently | `validate_raw()` checks schema, ranges and genres |

## New analysis
- Six explicit business questions with evidence (trend tests, Mann-Whitney U, Spearman, effect sizes)
- Price, rating and genre trends over time; longevity ("one-year wonders" vs evergreens); engagement (reviews)
- Caveat discovered and documented: reviews/ratings are a single 2020 snapshot

## Engineering
- Code split into a package (`src/bestsellers/`) with small, documented, testable functions
- SQL versions of key queries (DuckDB) with automated parity tests against pandas
- 22 pytest tests, ruff linting, GitHub Actions CI on Python 3.11 & 3.12
- `python -m bestsellers.report` regenerates every figure/table/finding; numbers in the write-up are computed, not typed
- Interactive Streamlit dashboard (filters, search, CSV download)
- README with findings, data dictionary, limitations

## Kept from v1
- The dataset and the original questions (author counts, rating by genre)
- The two CSV exports: `reports/tables/top_authors.csv` and `reports/tables/avg_rating_by_genre.csv`, now corrected
