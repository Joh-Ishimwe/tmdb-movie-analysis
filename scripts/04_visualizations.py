"""
Step 4: Data Visualization

Loads the KPI-enriched dataset produced by 03_kpis.py and renders the
project's charts with Matplotlib: Revenue vs. Budget, ROI Distribution by
Genre, Popularity vs. Rating, Yearly Trends in Box Office Performance, and
Franchise vs. Standalone Success. Figures are saved as PNGs to
reports/figures/. One fixed accent color is used per series/entity
throughout (never re-cycled per category), so the same color always means
the same thing across charts.
"""

import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless: never pop up a GUI window, just save PNGs
import matplotlib.pyplot as plt
import pandas as pd

# Windows terminals default to cp1252, which can't print some movie titles
# (accented characters, etc.). Force UTF-8 so this script doesn't crash on
# print() the way Jupyter (UTF-8 by default) never does.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# 1. File locations

KPI_FILE = Path("data/processed/tmdb_movies_with_kpis.csv")
FIGURES_DIR = "reports/figures"

ACCENT = "#2f6f9f"    # single-series charts
ACCENT_B = "#c76a3f"  # second entity in Franchise-vs-Standalone charts


# 2. Load the KPI-enriched dataset

def load_kpi_data():
    if not KPI_FILE.exists():
        raise FileNotFoundError(
            f"{KPI_FILE} not found. Run 03_kpis.py first."
        )

    df = pd.read_csv(KPI_FILE)
    # release_date round-trips through CSV as plain text -- restore it to
    # a real datetime so the yearly-trend chart can group by .dt.year.
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')

    print(f"Loaded {len(df)} movies from {KPI_FILE}")
    return df


# 3. Chart style
# Applied once, shared by every chart in this script.

def apply_chart_style():
    os.makedirs(FIGURES_DIR, exist_ok=True)

    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "#444444",
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": "#e3e3e3",
        "grid.linewidth": 0.7,
        "font.size": 11,
    })


# 4. Revenue vs. Budget
# Only the top 5 movies by revenue are directly labeled -- labeling all of
# them would clutter the plot given how tightly some points cluster.

def plot_revenue_vs_budget(df):
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(df['budget_musd'], df['revenue_musd'], s=80, color=ACCENT, alpha=0.85,
               edgecolor="white", linewidth=0.8, zorder=3)

    top5 = df.nlargest(5, 'revenue_musd')
    for _, row in top5.iterrows():
        ax.annotate(row['title'], (row['budget_musd'], row['revenue_musd']),
                    fontsize=8, xytext=(6, 6), textcoords='offset points', color="#333333")

    ax.set_xlabel("Budget (million USD)")
    ax.set_ylabel("Revenue (million USD)")
    ax.set_title("Revenue vs. Budget")
    fig.tight_layout()
    fig.savefig(f"{FIGURES_DIR}/revenue_vs_budget.png", dpi=150)
    plt.close(fig)
    print(f"Saved {FIGURES_DIR}/revenue_vs_budget.png")


# 5. ROI Distribution by Genre
# Each movie usually has multiple genres (genres is '|'-separated), so a
# movie's ROI counts toward every genre it belongs to -- done here with
# .explode(). Caveat: with a small dataset spread across many genres, most
# genres have just a handful of data points, so these boxes are
# illustrative rather than statistically robust.

def plot_roi_by_genre(df):
    genre_roi = df[['title', 'genres', 'roi']].dropna(subset=['genres', 'roi']).copy()
    genre_roi['genres'] = genre_roi['genres'].str.split('|')
    genre_roi = genre_roi.explode('genres').rename(columns={'genres': 'genre'})

    genre_order = genre_roi.groupby('genre')['roi'].median().sort_values(ascending=False).index
    data_by_genre = [genre_roi.loc[genre_roi['genre'] == g, 'roi'].values for g in genre_order]

    fig, ax = plt.subplots(figsize=(9, 5))
    bp = ax.boxplot(data_by_genre, tick_labels=list(genre_order), patch_artist=True, widths=0.5)

    for box in bp['boxes']:
        box.set(facecolor=ACCENT, alpha=0.5, edgecolor=ACCENT)
    for median in bp['medians']:
        median.set(color="#1a1a1a", linewidth=1.5)

    ax.set_ylabel("ROI (Revenue / Budget)")
    ax.set_title("ROI Distribution by Genre")
    plt.setp(ax.get_xticklabels(), rotation=35, ha='right')
    fig.tight_layout()
    fig.savefig(f"{FIGURES_DIR}/roi_by_genre.png", dpi=150)
    plt.close(fig)
    print(f"Saved {FIGURES_DIR}/roi_by_genre.png")


# 6. Popularity vs. Rating

def plot_popularity_vs_rating(df):
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(df['vote_average'], df['popularity'], s=80, color=ACCENT, alpha=0.85,
               edgecolor="white", linewidth=0.8, zorder=3)

    ax.set_xlabel("Average Rating (vote_average)")
    ax.set_ylabel("Popularity")
    ax.set_title("Popularity vs. Rating")
    fig.tight_layout()
    fig.savefig(f"{FIGURES_DIR}/popularity_vs_rating.png", dpi=150)
    plt.close(fig)
    print(f"Saved {FIGURES_DIR}/popularity_vs_rating.png")

    print("Correlation (rating, popularity):", df['vote_average'].corr(df['popularity']).round(3))


# 7. Yearly Trends in Box Office Performance
# Year is derived on the fly from release_date rather than a separate
# stored column. Caveat: a small, hand-picked set of blockbusters is not a
# representative sample of each year's full box office -- so this chart
# shows this dataset's revenue by year, not the industry's.

def plot_yearly_revenue_trend(df):
    yearly_revenue = (
        df.dropna(subset=['release_date'])
          .groupby(df['release_date'].dt.year)['revenue_musd']
          .sum()
          .sort_index()
    )

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(yearly_revenue.index.astype(str), yearly_revenue.values, color=ACCENT)

    for bar, v in zip(bars, yearly_revenue.values):
        ax.annotate(f"{v:,.0f}", (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    ha='center', va='bottom', fontsize=8, color="#333333")

    ax.set_xlabel("Release Year")
    ax.set_ylabel("Total Revenue (million USD)")
    ax.set_title("Total Box-Office Revenue by Release Year (this dataset)")
    plt.xticks(rotation=45)
    fig.tight_layout()
    fig.savefig(f"{FIGURES_DIR}/yearly_revenue_trend.png", dpi=150)
    plt.close(fig)
    print(f"Saved {FIGURES_DIR}/yearly_revenue_trend.png")


# 8. Franchise vs. Standalone: Comparison Across Metrics
# A movie is treated as part of a franchise if belongs_to_collection is not
# null. The five metrics live on very different scales (revenue in hundreds
# of millions, rating out of 10), so instead of one bar chart with
# mismatched axes, this uses small multiples -- one subplot per metric,
# sharing a single color per group (Franchise / Standalone) across all five.

def compute_franchise_vs_standalone(df):
    franchise_vs_standalone = df.groupby('is_franchise').agg(
        n_movies=('title', 'count'),
        mean_revenue_musd=('revenue_musd', 'mean'),
        median_roi=('roi', 'median'),
        mean_budget_musd=('budget_musd', 'mean'),
        mean_popularity=('popularity', 'mean'),
        mean_rating=('vote_average', 'mean'),
    )
    franchise_vs_standalone.index = franchise_vs_standalone.index.map(
        {True: 'Franchise', False: 'Standalone'}
    )
    franchise_vs_standalone.index.name = 'group'
    return franchise_vs_standalone


def plot_franchise_vs_standalone(franchise_vs_standalone):
    metrics = [
        ('mean_revenue_musd', 'Mean Revenue\n(million USD)'),
        ('median_roi', 'Median ROI'),
        ('mean_budget_musd', 'Mean Budget\n(million USD)'),
        ('mean_popularity', 'Mean Popularity'),
        ('mean_rating', 'Mean Rating'),
    ]

    categories = franchise_vs_standalone.index.tolist()
    colors = {'Franchise': ACCENT, 'Standalone': ACCENT_B}

    fig, axes = plt.subplots(1, len(metrics), figsize=(18, 4.5))
    for ax, (col, label) in zip(axes, metrics):
        values = franchise_vs_standalone.loc[categories, col]
        bars = ax.bar(categories, values, color=[colors[c] for c in categories])
        ax.set_title(label, fontsize=10)
        for bar, v in zip(bars, values):
            ax.annotate(f"{v:,.1f}", (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        ha='center', va='bottom', fontsize=8)

    fig.suptitle("Franchise vs. Standalone Performance", y=1.03)
    fig.tight_layout()
    fig.savefig(f"{FIGURES_DIR}/franchise_vs_standalone.png", dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved {FIGURES_DIR}/franchise_vs_standalone.png")


# 9. Main pipeline

def run_visualizations():
    df = load_kpi_data()
    apply_chart_style()

    plot_revenue_vs_budget(df)
    plot_roi_by_genre(df)
    plot_popularity_vs_rating(df)
    plot_yearly_revenue_trend(df)

    franchise_vs_standalone = compute_franchise_vs_standalone(df)
    plot_franchise_vs_standalone(franchise_vs_standalone)

    print(f"\nAll figures saved to {FIGURES_DIR}/")


def main():
    run_visualizations()


if __name__ == "__main__":
    main()
