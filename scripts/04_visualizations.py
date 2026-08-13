"""
Step 4: Data Visualization.

Thin CLI wrapper around tmdb_pipeline.visualization: handles file I/O.
All the actual plotting logic lives in tmdb_pipeline/visualization.py,
so it's directly importable and testable (e.g. against a tmp_path)
without going through this script.
"""

import sys
from pathlib import Path

import pandas as pd

from tmdb_pipeline.visualization import (
    apply_chart_style,
    plot_franchise_vs_standalone,
    plot_popularity_vs_rating,
    plot_revenue_vs_budget,
    plot_roi_by_genre,
    plot_yearly_revenue_trend,
)

# Windows terminals default to cp1252, which can't print some movie titles
# (accented characters, etc.). Force UTF-8 so this script doesn't crash on
# print() the way Jupyter (UTF-8 by default) never does.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


KPI_FILE = Path("data/processed/tmdb_movies_with_kpis.csv")
FIGURES_DIR = "reports/figures"


def load_kpi_data():
    if not KPI_FILE.exists():
        raise FileNotFoundError(f"{KPI_FILE} not found. Run 03_kpis.py first.")

    df = pd.read_csv(KPI_FILE)
    # release_date round-trips through CSV as plain text -- restore it to
    # a real datetime so the yearly-trend chart can group by .dt.year.
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')

    print(f"Loaded {len(df)} movies from {KPI_FILE}")
    return df


def main():
    df = load_kpi_data()
    apply_chart_style(FIGURES_DIR)

    print(f"Saved {plot_revenue_vs_budget(df, FIGURES_DIR)}")
    print(f"Saved {plot_roi_by_genre(df, FIGURES_DIR)}")
    print(f"Saved {plot_popularity_vs_rating(df, FIGURES_DIR)}")
    print("Correlation (rating, popularity):", df['vote_average'].corr(df['popularity']).round(3))
    print(f"Saved {plot_yearly_revenue_trend(df, FIGURES_DIR)}")
    print(f"Saved {plot_franchise_vs_standalone(df, FIGURES_DIR)}")

    print(f"\nAll figures saved to {FIGURES_DIR}/")


if __name__ == "__main__":
    main()
