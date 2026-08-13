"""
Step 3: KPI Implementation & Analysis

Loads the cleaned dataset produced by 02_clean_data.py and computes the
project's KPIs: best/worst performing movies, advanced filtering/search
queries, franchise vs. standalone performance, and the most successful
franchises & directors. Saves an enriched CSV (with profit_musd, roi,
and is_franchise added) so Step 4 (visualization) can load it directly.
"""

import sys
from pathlib import Path

import pandas as pd

# Windows terminals default to cp1252, which can't print some movie titles/
# cast names (accented characters, etc.). Force UTF-8 so this script
# doesn't crash on print() the way Jupyter (UTF-8 by default) never does.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# 1. File locations

CLEAN_FILE = Path("data/processed/tmdb_movies_clean.csv")
PROCESSED_DIR = Path("data/processed")
KPI_FILE = PROCESSED_DIR / "tmdb_movies_with_kpis.csv"


# 2. Load the cleaned dataset

def load_clean_data():
    if not CLEAN_FILE.exists():
        raise FileNotFoundError(
            f"{CLEAN_FILE} not found. Run 02_clean_data.py first."
        )

    df = pd.read_csv(CLEAN_FILE)
    print(f"Loaded {len(df)} movies from {CLEAN_FILE}")
    return df


# 3. A reusable ranking function (UDF)
# Rather than repeating .sort_values().head() for every KPI (revenue,
# budget, profit, ROI, votes, ratings, popularity), one function handles
# them all. min_budget covers the brief's ROI requirement
# ("only movies with Budget >= 10M").

def top_movies(dataframe, column, n=5, ascending=False, min_budget=None):
    """
    Returns the top (or bottom) n movies ranked by a given column.

    dataframe   : the DataFrame to rank
    column      : which column to sort by (e.g. 'revenue_musd')
    n           : how many rows to return
    ascending   : False = highest first, True = lowest first
    min_budget  : optional filter, e.g. only movies with budget >= 10 (million)
    """
    data = dataframe.copy()

    if min_budget is not None:
        data = data[data['budget_musd'] >= min_budget]

    return data.sort_values(column, ascending=ascending).head(n)[['title', column]]


# 4. Profit and ROI
# Calculated with direct vectorized arithmetic before ranking. ROI rankings
# are restricted to movies with budget_musd >= 10 per the project brief,
# using the min_budget parameter built into the UDF.

def add_profit_and_roi(df):
    df['profit_musd'] = df['revenue_musd'] - df['budget_musd']
    df['roi'] = df['revenue_musd'] / df['budget_musd']
    return df


# 5. Best/Worst Performing Movies

def best_worst_performing(df):
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


# 6. Advanced Movie Filtering & Search Queries
# Caveat: the movies in this dataset are the specific blockbuster franchise
# entries chosen in the project brief. Niche queries like "Bruce Willis
# sci-fi" or "Tarantino/Uma Thurman" were never fetched, so both searches
# are expected to return zero rows on this dataset -- that's a property of
# which movie IDs the brief specifies, not a bug in the filtering logic.

def advanced_search_queries(df):
    # Search 1: best-rated Science Fiction Action movies starring Bruce Willis
    search_1 = df[
        df['genres'].str.contains('Science Fiction', na=False)
        & df['genres'].str.contains('Action', na=False)
        & df['cast'].str.contains('Bruce Willis', na=False)
    ].sort_values('vote_average', ascending=False)

    print(f"\n--- Search 1: Sci-Fi Action starring Bruce Willis ---")
    print(f"Matches: {len(search_1)}")
    print(search_1[['title', 'genres', 'vote_average', 'cast']])

    # Search 2: movies starring Uma Thurman, directed by Quentin Tarantino,
    # shortest runtime first
    search_2 = df[
        df['cast'].str.contains('Uma Thurman', na=False)
        & (df['director'] == 'Quentin Tarantino')
    ].sort_values('runtime', ascending=True)

    print(f"\n--- Search 2: Uma Thurman directed by Quentin Tarantino ---")
    print(f"Matches: {len(search_2)}")
    print(search_2[['title', 'director', 'runtime', 'cast']])


# 7. Franchise vs. Standalone Movie Performance
# A movie is treated as part of a franchise if belongs_to_collection is
# not null.

def franchise_vs_standalone_performance(df):
    df['is_franchise'] = df['belongs_to_collection'].notna()

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

    print("\n--- Franchise vs. Standalone Performance ---")
    print(franchise_vs_standalone)
    return franchise_vs_standalone


# 8. Most Successful Movie Franchises
# Grouped by belongs_to_collection, ranked by total revenue.

def most_successful_franchises(df):
    franchise_success = df[df['belongs_to_collection'].notna()].groupby(
        'belongs_to_collection'
    ).agg(
        n_movies=('title', 'count'),
        total_budget_musd=('budget_musd', 'sum'),
        mean_budget_musd=('budget_musd', 'mean'),
        total_revenue_musd=('revenue_musd', 'sum'),
        mean_revenue_musd=('revenue_musd', 'mean'),
        mean_rating=('vote_average', 'mean'),
    ).sort_values('total_revenue_musd', ascending=False)

    print("\n--- Most Successful Movie Franchises ---")
    print(franchise_success)
    return franchise_success


# 9. Most Successful Directors
# Grouped by director, ranked by total revenue.

def most_successful_directors(df):
    director_success = df.groupby('director').agg(
        n_movies=('title', 'count'),
        total_revenue_musd=('revenue_musd', 'sum'),
        mean_rating=('vote_average', 'mean'),
    ).sort_values('total_revenue_musd', ascending=False)

    print("\n--- Most Successful Directors ---")
    print(director_success)
    return director_success


# 10. Main pipeline

def run_kpis():
    df = load_clean_data()
    df = add_profit_and_roi(df)

    best_worst_performing(df)
    advanced_search_queries(df)
    franchise_vs_standalone_performance(df)
    most_successful_franchises(df)
    most_successful_directors(df)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(KPI_FILE, index=False)
    print(f"\nSaved {len(df)} rows to {KPI_FILE}")

    return df


def main():
    run_kpis()


if __name__ == "__main__":
    main()
