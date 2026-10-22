# Data

`raw/bestsellers.csv`: Amazon's annual Top-50 bestselling books, 2009–2019 (550 rows × 7 columns),
originally scraped from Amazon and published on Kaggle as
**"Amazon Top 50 Bestselling Books 2009 - 2019"** (Souter Saalu, 2020).

| Column | Type | Notes |
|---|---|---|
| `Name` | text | Book title (renamed `title`) |
| `Author` | text | Two authors have spelling variants, unified during cleaning |
| `User Rating` | float | Amazon star rating, 1–5 (renamed `rating`) |
| `Reviews` | int | Number of written reviews |
| `Price` | int | List price in USD; 12 rows are $0 |
| `Year` | int | Year the book was on the Top-50 list |
| `Genre` | text | `Fiction` or `Non Fiction` |

### Known quirks (all handled in `src/bestsellers/data.py`)
- One row per **book per year**, so evergreen titles repeat up to 10 times.
- `Reviews` and `User Rating` were captured **once (2020)** and repeated for every year, so they are not per-year values.
- Author spelling variants: `J.K. Rowling` / `J. K. Rowling`, `George R.R. Martin` / `George R. R. Martin`.
- One title appears with two capitalisations (*The 5 Love Languages*).
- 3 book-year pairs appear twice (two editions on the same year's list).

Check the license on the Kaggle dataset page before redistributing the CSV.
