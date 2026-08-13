"""
Step 4: Data Visualization.

One fixed accent color per series throughout, so color always means the
same thing across charts. figures_dir is a parameter, not a module
constant, so these are testable against a tmp_path.
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


def plot_revenue_vs_budget(df, figures_dir):
    # Only the top 5 by revenue are labeled -- labeling all 18 would clutter it.
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


def plot_roi_by_genre(df, figures_dir):
    # A multi-genre movie's ROI counts toward each of its genres (explode).
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


def plot_popularity_vs_rating(df, figures_dir):
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(df['vote_average'], df['popularity'], s=80, color=ACCENT, alpha=0.85,
               edgecolor="white", linewidth=0.8, zorder=3)

    ax.set_xlabel("Average Rating (out of 10)")
    ax.set_ylabel("Popularity (TMDB popularity score)")
    ax.set_title("Popularity vs. Rating")
    fig.tight_layout()
    path = f"{figures_dir}/popularity_vs_rating.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_yearly_revenue_trend(df, figures_dir):
    # This dataset's revenue by year, not an industry-wide trend.
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


def plot_franchise_vs_standalone(df, figures_dir):
    # Small multiples (one subplot per metric) since revenue/ROI/rating
    # live on very different scales -- one bar chart wouldn't work.
    franchise_vs_standalone = franchise_vs_standalone_performance(df)

    metrics = [
        ('mean_revenue_musd', 'Mean Revenue\n(million USD)'),
        ('median_roi', 'Median ROI'),
        ('mean_budget_musd', 'Mean Budget\n(million USD)'),
        ('mean_popularity', 'Mean Popularity\n(TMDB score)'),
        ('mean_rating', 'Mean Rating\n(out of 10)'),
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
