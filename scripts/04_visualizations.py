"""
Step 4: Data Visualization.

Thin wrapper: loads KPI data, calls tmdb_pipeline.visualization to save charts.
"""

from pathlib import Path

import pandas as pd

from tmdb_pipeline.cli import force_utf8_stdout, log_loaded, require_file
from tmdb_pipeline.visualization import (
    apply_chart_style,
    plot_franchise_vs_standalone,
    plot_popularity_vs_rating,
    plot_revenue_vs_budget,
    plot_roi_by_genre,
    plot_yearly_revenue_trend,
)

force_utf8_stdout()


KPI_FILE = Path("data/processed/tmdb_movies_with_kpis.csv")
FIGURES_DIR = "reports/figures"


def load_kpi_data():
    require_file(KPI_FILE, "03_kpis.py")

    df = pd.read_csv(KPI_FILE)
    # CSV round-trips release_date as text -- restore it for .dt.year below.
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')

    log_loaded(len(df), KPI_FILE)
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
