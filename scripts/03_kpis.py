"""
Step 3: KPI Implementation & Analysis.

Thin CLI wrapper around tmdb_pipeline.kpis: handles file I/O and prints
the results. All the actual KPI computation lives in tmdb_pipeline/kpis.py
as pure, printless functions -- directly importable and testable
without going through this script.
"""

import sys
from pathlib import Path

import pandas as pd

from tmdb_pipeline.kpis import (
    add_profit_and_roi,
    franchise_vs_standalone_performance,
    most_successful_directors,
    most_successful_franchises,
    search_by_cast_and_director,
    search_scifi_action_with_actor,
    top_movies,
)

# Windows terminals default to cp1252, which can't print some movie titles/
# cast names (accented characters, etc.). Force UTF-8 so this script
# doesn't crash on print() the way Jupyter (UTF-8 by default) never does.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


CLEAN_FILE = Path("data/processed/tmdb_movies_clean.csv")
PROCESSED_DIR = Path("data/processed")
KPI_FILE = PROCESSED_DIR / "tmdb_movies_with_kpis.csv"


def load_clean_data():
    if not CLEAN_FILE.exists():
        raise FileNotFoundError(f"{CLEAN_FILE} not found. Run 02_clean_data.py first.")

    df = pd.read_csv(CLEAN_FILE)
    print(f"Loaded {len(df)} movies from {CLEAN_FILE}")
    return df


def print_best_worst_performing(df):
    print("\n--- Highest Revenue ---")
    print(top_movies(df, 'revenue_musd', n=5))

    print("\n--- Highest Budget ---")
    print(top_movies(df, 'budget_musd', n=5))

    print("\n--- Most Voted ---")
    print(top_movies(df, 'vote_count', n=5))

    # Highest Rated & Lowest Rated (only movies with >= 10 votes, per the brief)
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
    # Caveat: the movies in this dataset are the specific blockbuster
    # franchise entries chosen in the project brief. Niche queries like
    # "Bruce Willis sci-fi" or "Tarantino/Uma Thurman" were never fetched,
    # so both searches are expected to return zero rows on this dataset --
    # that's a property of which movie IDs the brief specifies, not a bug
    # in the filtering logic.
    search_1 = search_scifi_action_with_actor(df, 'Bruce Willis')
    print("\n--- Search 1: Sci-Fi Action starring Bruce Willis ---")
    print(f"Matches: {len(search_1)}")
    print(search_1)

    search_2 = search_by_cast_and_director(df, 'Uma Thurman', 'Quentin Tarantino')
    print("\n--- Search 2: Uma Thurman directed by Quentin Tarantino ---")
    print(f"Matches: {len(search_2)}")
    print(search_2)


def main():
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

    # franchise_vs_standalone_performance() computes is_franchise on its
    # own copy (pure function, no side effects on the caller's df) -- add
    # it here explicitly so the saved CSV still carries it for Step 4.
    df['is_franchise'] = df['belongs_to_collection'].notna()

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(KPI_FILE, index=False)
    print(f"\nSaved {len(df)} rows to {KPI_FILE}")


if __name__ == "__main__":
    main()
