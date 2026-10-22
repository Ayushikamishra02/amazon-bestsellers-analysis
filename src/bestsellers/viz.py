"""Publication-quality figures with one consistent style."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from . import analysis as A  # noqa: E402

FICTION, NONFICTION, ACCENT, GREY = "#7c3aed", "#0d9488", "#f59e0b", "#94a3b8"
GENRE_COLORS = {"Fiction": FICTION, "Non Fiction": NONFICTION}

plt.rcParams.update({
    "figure.dpi": 120, "savefig.dpi": 150, "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "axes.titleweight": "bold", "axes.titlesize": 11,
    "legend.frameon": False,
})


def _save(fig, out: Path, name: str) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{name}.png"
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def genre_mix(appearances: pd.DataFrame, out: Path) -> Path:
    share = A.genre_share_by_year(appearances) * 100
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.bar(share.index, share["Non Fiction"], color=NONFICTION, label="Non Fiction")
    ax.bar(share.index, share["Fiction"], bottom=share["Non Fiction"], color=FICTION, label="Fiction")
    ax.axhline(50, color="white", lw=1, ls="--")
    for x, v in zip(share.index, share["Non Fiction"]):
        ax.text(x, v / 2, f"{v:.0f}%", ha="center", va="center", color="white", fontsize=8)
    ax.set(title="Genre mix of the Top-50 list each year", ylabel="% of list", ylim=(0, 100),
           xticks=share.index)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
    ax.grid(False)
    return _save(fig, out, "genre_mix_by_year")


def ratings(appearances: pd.DataFrame, books: pd.DataFrame, out: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
    r = books.assign(r=books["rating"].round(1))
    counts = pd.crosstab(r["r"], r["genre"]).reindex(np.round(np.arange(3.3, 4.95, 0.1), 1), fill_value=0)
    x = np.arange(len(counts))
    for i, (g, c) in enumerate(GENRE_COLORS.items()):
        axes[0].bar(x + (i - 0.5) * 0.4, counts[g], 0.4, color=c, label=g)
    axes[0].set_xticks(x[::2], [f"{v:.1f}" for v in counts.index[::2]])
    axes[0].set(title="Ratings are crowded near the top (one count per book)",
                xlabel="Average user rating", ylabel="Books")
    axes[0].legend(loc="upper left")

    ry = A.rating_by_year(appearances)
    axes[1].plot(ry.index, ry["mean"], "o-", color=FICTION, lw=2, label="Mean rating")
    axes[1].set(title="Ratings of list books rose over the decade", ylabel="Mean rating", xticks=ry.index)
    axes[1].tick_params(axis="x", rotation=45)
    ax2 = axes[1].twinx()
    ax2.bar(ry.index, ry["share_4_8_plus"] * 100, color=ACCENT, alpha=0.3, label="% rated 4.8+")
    ax2.set_ylabel("% of list rated 4.8+")
    ax2.grid(False)
    ax2.spines["right"].set_visible(True)
    axes[1].set_zorder(ax2.get_zorder() + 1)
    axes[1].patch.set_visible(False)
    h1, l1 = axes[1].get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    axes[1].legend(h1 + h2, l1 + l2, loc="upper left")
    return _save(fig, out, "ratings")


def prices(appearances: pd.DataFrame, books: pd.DataFrame, out: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), gridspec_kw={"width_ratios": [1.3, 1]})
    py = A.price_by_year(appearances)
    for g, c in GENRE_COLORS.items():
        axes[0].plot(py.index, py[g], "o-", color=c, lw=2, label=g)
    axes[0].set(title="Median list price is falling (paid books)", ylabel="Median price (USD)",
                xticks=py.index)
    axes[0].tick_params(axis="x", rotation=45)
    axes[0].legend()

    paid = books[~books["is_free"]]
    data = [paid.loc[paid["genre"] == g, "price"] for g in GENRE_COLORS]
    bp = axes[1].boxplot(data, tick_labels=list(GENRE_COLORS), patch_artist=True, widths=0.5,
                         medianprops={"color": "black"}, flierprops={"markersize": 3})
    for patch, c in zip(bp["boxes"], GENRE_COLORS.values()):
        patch.set_facecolor(c)
        patch.set_alpha(0.6)
    axes[1].set(title="Price by genre (one count per book)", ylabel="Price (USD, log scale)", yscale="log")
    top = paid.nlargest(2, "price")
    for _, r in top.iterrows():
        x = 1 if r["genre"] == "Fiction" else 2
        axes[1].annotate(r["title"][:28] + "...", (x, r["price"]), xytext=(8, 0),
                         textcoords="offset points", fontsize=7, va="center")
    return _save(fig, out, "prices")


def authors(appearances: pd.DataFrame, out: Path) -> Path:
    t = A.top_authors(appearances, 12).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    y = np.arange(len(t))
    ax.barh(y + 0.2, t["list_appearances"], 0.4, color=FICTION, label="List appearances")
    ax.barh(y - 0.2, t["unique_titles"], 0.4, color=ACCENT, label="Unique titles")
    ax.set_yticks(y, t.index)
    ax.set(title="Top authors: many list slots, often from few titles", xlabel="Count")
    ax.legend(loc="lower right")
    return _save(fig, out, "top_authors")


def longevity(books: pd.DataFrame, out: Path) -> Path:
    dist = A.longevity_distribution(books)
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    colors = [GREY if k == 1 else (ACCENT if k >= 5 else NONFICTION) for k in dist.index]
    ax.bar(dist.index, dist.values, color=colors)
    for k, v in dist.items():
        ax.text(k, v + 3, str(v), ha="center", fontsize=8)
    ax.set(title=f"Most bestsellers are one-year wonders ({(books['years_on_list'] == 1).mean():.0%} appear once)",
           xlabel="Years on the Top-50 list (2009-2019)", ylabel="Books", xticks=dist.index)
    return _save(fig, out, "longevity")


def reviews_vs_rating(books: pd.DataFrame, out: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for g, c in GENRE_COLORS.items():
        b = books[books["genre"] == g]
        ax.scatter(b["reviews"], b["rating"], s=12 + b["years_on_list"] * 12, color=c, alpha=0.55,
                   edgecolor="white", lw=0.4, label=g)
    offsets = [(-20, -40), (-25, -25), (-60, 30)]   # Crawdads, Girl on the Train, Becoming
    for (_, r), off in zip(books.nlargest(3, "reviews").iterrows(), offsets):
        ax.annotate(r["title"][:28], (r["reviews"], r["rating"]), xytext=off, textcoords="offset points",
                    fontsize=8, ha="right", va="center",
                    arrowprops={"arrowstyle": "-", "color": "#475569", "lw": 0.8})
    ax.set_ylim(top=5.05)
    ax.set(xscale="log", title="More reviews does not mean a higher rating (bubble size = years on list)",
           xlabel="Number of reviews (log scale, 2020 snapshot)", ylabel="Average rating")
    ax.legend(loc="lower left")
    return _save(fig, out, "reviews_vs_rating")


def correlation_heatmap(books: pd.DataFrame, out: Path) -> Path:
    c = A.correlations(books)
    fig, ax = plt.subplots(figsize=(4.8, 4))
    im = ax.imshow(c, cmap="RdBu_r", vmin=-1, vmax=1)
    labels = [s.replace("_", " ") for s in c.columns]
    ax.set_xticks(range(len(c)), labels, rotation=30, ha="right")
    ax.set_yticks(range(len(c)), labels)
    for i in range(len(c)):
        for j in range(len(c)):
            ax.text(j, i, f"{c.iat[i, j]:.2f}", ha="center", va="center", fontsize=9)
    ax.grid(False)
    ax.set_title("Spearman correlations (paid books)")
    fig.colorbar(im, ax=ax, shrink=0.8)
    return _save(fig, out, "correlations")


def all_figures(appearances: pd.DataFrame, books: pd.DataFrame, out: Path) -> list[Path]:
    return [
        genre_mix(appearances, out), ratings(appearances, books, out), prices(appearances, books, out),
        authors(appearances, out), longevity(books, out), reviews_vs_rating(books, out),
        correlation_heatmap(books, out),
    ]
