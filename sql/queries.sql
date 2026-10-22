-- ---------------------------------------------------------------------------
-- Amazon Top-50 Bestsellers 2009-2019: the same analyses in SQL (DuckDB dialect)
-- Run with:  python -m bestsellers.sql      (or paste into the DuckDB CLI)
-- Tables available: appearances (one row per book-year), books (one row per title)
-- Each query is preceded by a "-- name: <id>" tag so Python can run them by name.
-- ---------------------------------------------------------------------------

-- name: genre_share_by_year
SELECT year,
       ROUND(AVG(CASE WHEN genre = 'Fiction' THEN 1 ELSE 0 END), 3)     AS fiction_share,
       ROUND(AVG(CASE WHEN genre = 'Non Fiction' THEN 1 ELSE 0 END), 3) AS nonfiction_share
FROM appearances
GROUP BY year
ORDER BY year;

-- name: rating_by_genre
-- Per-BOOK average (each title counted once), unlike v1 which averaged list slots
SELECT genre,
       COUNT(*)                AS books,
       ROUND(AVG(rating), 3)   AS mean_rating,
       ROUND(MEDIAN(rating), 3) AS median_rating
FROM books
GROUP BY genre
ORDER BY genre;

-- name: top_authors
SELECT author,
       COUNT(*)              AS list_appearances,
       COUNT(DISTINCT title) AS unique_titles,
       COUNT(DISTINCT year)  AS years_active
FROM appearances
GROUP BY author
ORDER BY list_appearances DESC, unique_titles DESC, author
LIMIT 10;

-- name: median_price_by_year
SELECT year, MEDIAN(price) AS median_price
FROM appearances
WHERE NOT is_free
GROUP BY year
ORDER BY year;

-- name: evergreens
-- Books that stayed on the list the longest, ranked with a window function
SELECT *
FROM (
    SELECT title, author, genre, years_on_list,
           DENSE_RANK() OVER (ORDER BY years_on_list DESC) AS longevity_rank
    FROM books
)
WHERE longevity_rank <= 3
ORDER BY years_on_list DESC, title;

-- name: newcomers_per_year
-- How many titles on each year's list are appearing for the first time?
WITH first_seen AS (
    SELECT title, author, MIN(year) AS first_year
    FROM appearances
    GROUP BY title, author
)
SELECT a.year,
       COUNT(DISTINCT CASE WHEN a.year = f.first_year THEN a.title END) AS new_titles,
       COUNT(DISTINCT a.title)                                         AS titles_on_list,
       ROUND(COUNT(DISTINCT CASE WHEN a.year = f.first_year THEN a.title END)
             / COUNT(DISTINCT a.title), 3)                             AS newcomer_share
FROM appearances a
JOIN first_seen f USING (title, author)
GROUP BY a.year
ORDER BY a.year;
