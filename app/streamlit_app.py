"""Interactive explorer for the Amazon Top-50 bestsellers (2009-2019).

Run:  streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import altair as alt
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bestsellers import analysis as A  # noqa: E402
from bestsellers.data import load, to_books  # noqa: E402

st.set_page_config(page_title="Amazon Bestsellers 2009-2019", page_icon="📚", layout="wide")
COLORS = alt.Scale(domain=["Fiction", "Non Fiction"], range=["#7c3aed", "#0d9488"])


@st.cache_data
def get_data():
    appearances, books, log = load()
    appearances = appearances.assign(genre=appearances["genre"].astype(str))
    return appearances, books.assign(genre=books["genre"].astype(str)), str(log)


appearances_all, _, cleaning_log = get_data()

# ---------------------------------------------------------------- sidebar
st.sidebar.header("Filters")
y0, y1 = st.sidebar.slider("Years", 2009, 2019, (2009, 2019))
genres = st.sidebar.multiselect("Genre", ["Fiction", "Non Fiction"], default=["Fiction", "Non Fiction"])
min_rating = st.sidebar.slider("Minimum rating", 3.3, 4.9, 3.3, 0.1)
search = st.sidebar.text_input("Search title or author")

mask = appearances_all["year"].between(y0, y1) & appearances_all["genre"].isin(genres) \
    & (appearances_all["rating"] >= min_rating)
if search:
    s = search.lower()
    mask &= appearances_all["title"].str.lower().str.contains(s, regex=False) \
        | appearances_all["author"].str.lower().str.contains(s, regex=False)
appearances = appearances_all[mask]
if appearances.empty:
    st.warning("No books match these filters.")
    st.stop()
books = to_books(appearances).assign(genre=lambda d: d["genre"].astype(str))

# ---------------------------------------------------------------- header + KPIs
st.title("📚 Amazon Top-50 Bestsellers, 2009–2019")
st.caption("550 list slots · 350 unique books · cleaned & analysed with pandas, SciPy and DuckDB")

k = st.columns(5)
k[0].metric("List slots", f"{len(appearances):,}")
k[1].metric("Unique books", f"{len(books):,}")
k[2].metric("Authors", f"{appearances['author'].nunique():,}")
k[3].metric("Median rating", f"{books['rating'].median():.2f}")
paid = books[~books["is_free"]]
k[4].metric("Median price", f"${paid['price'].median():.0f}" if len(paid) else "-")

tab_trends, tab_books, tab_authors, tab_data = st.tabs(["Trends", "Books", "Authors", "Data & cleaning"])

with tab_trends:
    c1, c2 = st.columns(2)
    share = (appearances.groupby(["year", "genre"]).size().rename("n").reset_index())
    c1.subheader("Genre mix by year")
    c1.altair_chart(
        alt.Chart(share).mark_bar().encode(
            x=alt.X("year:O", title=None), y=alt.Y("n:Q", stack="normalize", title="Share of list",
                                                     axis=alt.Axis(format="%")),
            color=alt.Color("genre:N", scale=COLORS, legend=alt.Legend(orient="bottom", title=None)),
            tooltip=["year", "genre", "n"]).properties(height=320), use_container_width=True)

    c2.subheader("Median price by year (paid books)")
    py = (appearances[~appearances["is_free"]].groupby(["year", "genre"])["price"].median()
          .rename("price").reset_index())
    c2.altair_chart(
        alt.Chart(py).mark_line(point=True, strokeWidth=3).encode(
            x=alt.X("year:O", title=None), y=alt.Y("price:Q", title="USD"),
            color=alt.Color("genre:N", scale=COLORS, legend=alt.Legend(orient="bottom", title=None)),
            tooltip=["year", "genre", alt.Tooltip("price:Q", format="$.2f")]).properties(height=320),
        use_container_width=True)

    st.subheader("Mean rating of list books by year")
    ry = appearances.groupby("year")["rating"].mean().rename("rating").reset_index()
    st.altair_chart(alt.Chart(ry).mark_line(point=True, strokeWidth=3, color="#7c3aed").encode(
        x=alt.X("year:O", title=None), y=alt.Y("rating:Q", scale=alt.Scale(zero=False), title="Mean rating"),
        tooltip=["year", alt.Tooltip("rating:Q", format=".2f")]).properties(height=220), use_container_width=True)

with tab_books:
    st.subheader("Reviews vs rating (each bubble is a book)")
    st.altair_chart(
        alt.Chart(books).mark_circle(opacity=0.6).encode(
            x=alt.X("reviews:Q", scale=alt.Scale(type="log"), title="Reviews (log)"),
            y=alt.Y("rating:Q", scale=alt.Scale(zero=False), title="Rating"),
            size=alt.Size("years_on_list:Q", title="Years on list"),
            color=alt.Color("genre:N", scale=COLORS),
            tooltip=["title", "author", "genre", "rating", "reviews", "price", "years_on_list"],
        ).interactive().properties(height=420), use_container_width=True)
    c1, c2 = st.columns(2)
    c1.markdown("**Longest on the list**")
    c1.dataframe(A.evergreens(books, 10), hide_index=True, use_container_width=True)
    c2.markdown("**Most reviewed**")
    c2.dataframe(A.most_reviewed(books, 10), hide_index=True, use_container_width=True)

with tab_authors:
    n = st.slider("Show top N authors", 5, 25, 12)
    ta = A.top_authors(appearances, n).reset_index()
    long = ta.melt(id_vars="author", value_vars=["list_appearances", "unique_titles"],
                   var_name="measure", value_name="count")
    long["measure"] = long["measure"].map({"list_appearances": "List appearances", "unique_titles": "Unique titles"})
    st.altair_chart(alt.Chart(long).mark_bar().encode(
        y=alt.Y("author:N", sort="-x", title=None, axis=alt.Axis(labelLimit=260, labelOverlap=False)),
        x=alt.X("count:Q", title="Count", axis=alt.Axis(tickMinStep=1)),
        color=alt.Color("measure:N", scale=alt.Scale(range=["#7c3aed", "#f59e0b"]),
                        legend=alt.Legend(orient="bottom", title=None)),
        yOffset="measure:N", tooltip=["author", "measure", "count"]).properties(height=42 * n),
        use_container_width=True)
    st.caption("List appearances ≠ books written: Gary Chapman has 11 appearances from just 2 titles.")

with tab_data:
    st.subheader("Cleaning log")
    st.markdown(cleaning_log)
    st.subheader("Filtered data")
    st.dataframe(appearances, hide_index=True, use_container_width=True)
    st.download_button("Download filtered CSV", appearances.to_csv(index=False), "bestsellers_filtered.csv",
                       "text/csv")
