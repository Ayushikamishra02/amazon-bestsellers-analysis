# Publishing guide (for you, not part of the analysis)

## Option A: replace your old repo (keeps stars/history, recommended)
```bash
git clone https://github.com/YOUR-USERNAME/panda-project.git
cd panda-project
git rm -r -q .                      # remove the old files from the working tree
# copy everything from this folder into it, then:
git add .
git commit -m "v2: rebuild as tested analysis package with stats, SQL and dashboard"
git push
```
Then rename the repo on GitHub (Settings → Repository name) to `amazon-bestsellers-analysis`.
GitHub redirects the old URL automatically.

## Option B: new repo
```bash
cd amazon-bestsellers-analysis
git init && git add . && git commit -m "Amazon bestsellers analysis v2"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/amazon-bestsellers-analysis.git
git push -u origin main
```

## After pushing
1. Replace `YOUR-USERNAME` / `YOUR-PROFILE` in `README.md`; un-comment the CI badge.
2. About → description: *Data-quality-first analysis of Amazon's Top-50 bestsellers 2009–2019 with pandas, SciPy, DuckDB SQL and a Streamlit dashboard.*
3. Topics: `data-analysis` `pandas` `eda` `sql` `duckdb` `statistics` `streamlit` `data-visualization` `python`
4. Deploy the dashboard on https://share.streamlit.io (main file: `app/streamlit_app.py`) and add the link to the README.

## Resume bullets
- Analysed 11 years of Amazon Top-50 bestseller data (550 records) in pandas; found that 73% of bestsellers chart for only one year and median prices fell 17%.
- Identified and corrected a unit-of-analysis error (book-years vs books) that overstated a genre rating gap 4×; documented all data-quality fixes in an automated cleaning log.
- Validated findings with non-parametric tests (Mann-Whitney U, Spearman) and effect sizes; re-implemented key queries in SQL (DuckDB) with automated pandas-SQL parity tests.
- Built a reproducible pipeline (one-command report, 22 tests, CI) and an interactive Streamlit dashboard.

## Interview talking points
- **"What was the hardest part?"** Realising the rows are book-years, not books. Show the v1 vs v2 table in the notebook.
- **"Why Mann-Whitney?"** Ratings are bounded (≤ 5), discrete and left-skewed; a t-test's assumptions don't hold.
- **"Why is the rating trend tricky?"** Ratings were scraped once in 2020, so the trend reflects which books made later lists, not rating inflation over time.
