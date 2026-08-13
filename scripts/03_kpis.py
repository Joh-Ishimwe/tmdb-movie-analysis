"""
Step 3: KPI Implementation & Analysis.

Thin wrapper: loads data, calls tmdb_pipeline.kpis, prints/saves results.
"""

import logging
from pathlib import Path

import pandas as pd

from tmdb_pipeline.cli import ensure_dir, force_utf8_stdout, log_loaded, require_file
from tmdb_pipeline.kpis import (
    add_profit_and_roi,
    franchise_vs_standalone_performance,
    most_successful_directors,
    most_successful_franchises,
    search_by_cast_and_director,
    search_scifi_action_with_actor,
    top_movies,
)
from tmdb_pipeline.logging_config import setup_logging

force_utf8_stdout()

logger = logging.getLogger("03_kpis")


CLEAN_FILE = Path("data/processed/tmdb_movies_clean.csv")
PROCESSED_DIR = Path("data/processed")
KPI_FILE = PROCESSED_DIR / "tmdb_movies_with_kpis.csv"


def load_clean_data():
    require_file(CLEAN_FILE)

    df = pd.read_csv(CLEAN_FILE)
    log_loaded(logger, len(df), CLEAN_FILE)
    return df


def print_best_worst_performing(df):
    print("\n--- Highest Revenue ---")
    print(top_movies(df, 'revenue_musd', n=5))

    print("\n--- Highest Budget ---")
    print(top_movies(df, 'budget_musd', n=5))

    print("\n--- Most Voted ---")
    print(top_movies(df, 'vote_count', n=5))

    rated = df[df['vote_count'] >= 10]
    print("\n--- Highest Rated (>= 10 votes) ---")
    print(top_movies(rated, 'vote_average', n=5))
    print("\n--- Lowest Rated (>= 10 votes) ---")
    print(top_movies(rated, 'vote_average', n=5, ascending=True))

    print("\n--- Most Popular ---")
    print(top_movies(df, 'popularity', n=5))

    print("\n--- Highest Profit ---")
    print(top_movies(df, 'profit_musd', n=5))

    print("\n--- Lowest Profit ---")
    print(top_movies(df, 'profit_musd', n=5, ascending=True))

    print("\n--- Highest ROI (budget >= 10M) ---")
    print(top_movies(df, 'roi', n=5, min_budget=10))

    print("\n--- Lowest ROI (budget >= 10M) ---")
    print(top_movies(df, 'roi', n=5, ascending=True, min_budget=10))


def print_advanced_search_queries(df):
    # Both searches return 0 rows on this dataset -- it's only the 18
    # blockbusters from the brief, not the full TMDb catalog.
    search_1 = search_scifi_action_with_actor(df, 'Bruce Willis')
    print("\n--- Search 1: Sci-Fi Action starring Bruce Willis ---")
    print(f"Matches: {len(search_1)}")
    print(search_1)

    search_2 = search_by_cast_and_director(df, 'Uma Thurman', 'Quentin Tarantino')
    print("\n--- Search 2: Uma Thurman directed by Quentin Tarantino ---")
    print(f"Matches: {len(search_2)}")
    print(search_2)


def run():
    setup_logging()

    try:
        df = load_clean_data()
        df = add_profit_and_roi(df)

        print_best_worst_performing(df)
        print_advanced_search_queries(df)

        print("\n--- Franchise vs. Standalone Performance ---")
        print(franchise_vs_standalone_performance(df))

        print("\n--- Most Successful Movie Franchises ---")
        print(most_successful_franchises(df))

        print("\n--- Most Successful Directors ---")
        print(most_successful_directors(df))

        # Add for the saved CSV -- franchise_vs_standalone_performance() only
        # computes this on its own copy.
        df['is_franchise'] = df['belongs_to_collection'].notna()

        ensure_dir(PROCESSED_DIR)
        df.to_csv(KPI_FILE, index=False)
        logger.info("Saved %d rows to %s", len(df), KPI_FILE)
    except Exception:
        logger.exception("Step 3 (KPIs) failed.")
        raise


if __name__ == "__main__":
    raise SystemExit(
        "This pipeline has one entry point: "
        "run 'python scripts/run_pipeline.py' or the 'tmdb-pipeline' command."
    )
