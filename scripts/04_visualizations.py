"""
Step 4: Data Visualization.

Thin wrapper: loads KPI data, calls tmdb_pipeline.visualization to save charts.
"""

import logging
from pathlib import Path

import pandas as pd

from tmdb_pipeline.cli import force_utf8_stdout, log_loaded, require_file
from tmdb_pipeline.logging_config import setup_logging
from tmdb_pipeline.visualization import (
    apply_chart_style,
    plot_franchise_vs_standalone,
    plot_popularity_vs_rating,
    plot_revenue_vs_budget,
    plot_roi_by_genre,
    plot_yearly_revenue_trend,
)

force_utf8_stdout()

logger = logging.getLogger("04_visualizations")


KPI_FILE = Path("data/processed/tmdb_movies_with_kpis.csv")
FIGURES_DIR = "reports/figures"


def load_kpi_data():
    require_file(KPI_FILE)

    df = pd.read_csv(KPI_FILE)
    # CSV round-trips release_date as text -- restore it for .dt.year below.
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')

    log_loaded(logger, len(df), KPI_FILE)
    return df


def run():
    setup_logging()

    try:
        df = load_kpi_data()
        apply_chart_style(FIGURES_DIR)

        logger.info("Saved %s", plot_revenue_vs_budget(df, FIGURES_DIR))
        logger.info("Saved %s", plot_roi_by_genre(df, FIGURES_DIR))
        logger.info("Saved %s", plot_popularity_vs_rating(df, FIGURES_DIR))
        print("Correlation (rating, popularity):", df['vote_average'].corr(df['popularity']).round(3))
        logger.info("Saved %s", plot_yearly_revenue_trend(df, FIGURES_DIR))
        logger.info("Saved %s", plot_franchise_vs_standalone(df, FIGURES_DIR))

        logger.info("All figures saved to %s/", FIGURES_DIR)
    except Exception:
        logger.exception("Step 4 (visualizations) failed.")
        raise


if __name__ == "__main__":
    raise SystemExit(
        "This pipeline has one entry point: "
        "run 'python scripts/run_pipeline.py' or the 'tmdb-pipeline' command."
    )
