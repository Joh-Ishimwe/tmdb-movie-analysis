"""
Step 4: Data Visualization.

One fixed accent color per series/entity throughout (never re-cycled per
category), so the same color always means the same thing across charts.
Every plot_* function takes figures_dir explicitly rather than reading a
module-level constant -- makes these testable against a tmp_path without
ever touching the real reports/ directory.
"""

import os

import matplotlib
matplotlib.use("Agg")  # headless: never pop up a GUI window, just save PNGs
import matplotlib.pyplot as plt

from tmdb_pipeline.kpis import franchise_vs_standalone_performance

ACCENT = "#2f6f9f"    # single-series charts
ACCENT_B = "#c76a3f"  # second entity in Franchise-vs-Standalone charts


def apply_chart_style(figures_dir):
    os.makedirs(figures_dir, exist_ok=True)

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


# Revenue vs. Budget
# Only the top 5 movies by revenue are directly labeled -- labeling all of
# them would clutter the plot given how tightly some points cluster.

def plot_revenue_vs_budget(df, figures_dir):
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
    path = f"{figures_dir}/revenue_vs_budget.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


# ROI Distribution by Genre
# Each movie usually has multiple genres (genres is '|'-separated), so a
# movie's ROI counts toward every genre it belongs to -- done here with
# .explode(). Caveat: with a small dataset spread across many genres, most
# genres have just a handful of data points, so these boxes are
# illustrative rather than statistically robust.

def plot_roi_by_genre(df, figures_dir):
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
    path = f"{figures_dir}/roi_by_genre.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


# Popularity vs. Rating

def plot_popularity_vs_rating(df, figures_dir):
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(df['vote_average'], df['popularity'], s=80, color=ACCENT, alpha=0.85,
               edgecolor="white", linewidth=0.8, zorder=3)

    ax.set_xlabel("Average Rating (vote_average)")
    ax.set_ylabel("Popularity")
    ax.set_title("Popularity vs. Rating")
    fig.tight_layout()
    path = f"{figures_dir}/popularity_vs_rating.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


# Yearly Trends in Box Office Performance
# Year is derived on the fly from release_date rather than a separate
# stored column. Caveat: a small, hand-picked set of blockbusters is not a
# representative sample of each year's full box office -- so this chart
# shows this dataset's revenue by year, not the industry's.

def plot_yearly_revenue_trend(df, figures_dir):
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
    path = f"{figures_dir}/yearly_revenue_trend.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


# Franchise vs. Standalone: Comparison Across Metrics
# The five metrics live on very different scales (revenue in hundreds of
# millions, rating out of 10), so instead of one bar chart with mismatched
# axes, this uses small multiples -- one subplot per metric, sharing a
# single color per group (Franchise / Standalone) across all five.
# Reuses kpis.franchise_vs_standalone_performance() rather than
# recomputing the same aggregation -- that duplication used to exist only
# because 03_kpis.py's numbered filename couldn't be imported.

def plot_franchise_vs_standalone(df, figures_dir):
    franchise_vs_standalone = franchise_vs_standalone_performance(df)

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
    path = f"{figures_dir}/franchise_vs_standalone.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path
