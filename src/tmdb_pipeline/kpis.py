"""
Step 3: KPI Implementation & Analysis.

Pure computation, no printing -- every function here takes a DataFrame
and returns a DataFrame. scripts/03_kpis.py decides what to print;
that split is what makes these directly unit-testable (assert on the
returned values) instead of only checkable by eyeballing console output.
"""


# A reusable ranking function (UDF)
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


# Profit and ROI
# Calculated with direct vectorized arithmetic before ranking. ROI rankings
# are restricted to movies with budget_musd >= 10 per the project brief,
# using the min_budget parameter built into the UDF.

def add_profit_and_roi(df):
    df['profit_musd'] = df['revenue_musd'] - df['budget_musd']
    df['roi'] = df['revenue_musd'] / df['budget_musd']
    return df


# Advanced Movie Filtering & Search Queries
# Caveat: the movies in this dataset are the specific blockbuster franchise
# entries chosen in the project brief. Niche queries like "Bruce Willis
# sci-fi" or "Tarantino/Uma Thurman" were never fetched, so both searches
# are expected to return zero rows on this dataset -- that's a property of
# which movie IDs the brief specifies, not a bug in the filtering logic.

def search_scifi_action_with_actor(df, actor_name):
    """Best-rated Science Fiction Action movies starring actor_name,
    highest rating first. Parameterized rather than hardcoded to
    'Bruce Willis' so the search itself is reusable/testable beyond the
    one name the project brief happens to ask for."""
    return df[
        df['genres'].str.contains('Science Fiction', na=False)
        & df['genres'].str.contains('Action', na=False)
        & df['cast'].str.contains(actor_name, na=False)
    ].sort_values('vote_average', ascending=False)[['title', 'genres', 'vote_average', 'cast']]


def search_by_cast_and_director(df, actor_name, director_name):
    """Movies starring actor_name, directed by director_name, shortest
    runtime first."""
    return df[
        df['cast'].str.contains(actor_name, na=False)
        & (df['director'] == director_name)
    ].sort_values('runtime', ascending=True)[['title', 'director', 'runtime', 'cast']]


# Franchise vs. Standalone Movie Performance
# A movie is treated as part of a franchise if belongs_to_collection is
# not null.

def franchise_vs_standalone_performance(df):
    df = df.copy()
    df['is_franchise'] = df['belongs_to_collection'].notna()

    result = df.groupby('is_franchise').agg(
        n_movies=('title', 'count'),
        mean_revenue_musd=('revenue_musd', 'mean'),
        median_roi=('roi', 'median'),
        mean_budget_musd=('budget_musd', 'mean'),
        mean_popularity=('popularity', 'mean'),
        mean_rating=('vote_average', 'mean'),
    )
    result.index = result.index.map({True: 'Franchise', False: 'Standalone'})
    result.index.name = 'group'
    return result


# Most Successful Movie Franchises
# Grouped by belongs_to_collection, ranked by total revenue.

def most_successful_franchises(df):
    return df[df['belongs_to_collection'].notna()].groupby(
        'belongs_to_collection'
    ).agg(
        n_movies=('title', 'count'),
        total_budget_musd=('budget_musd', 'sum'),
        mean_budget_musd=('budget_musd', 'mean'),
        total_revenue_musd=('revenue_musd', 'sum'),
        mean_revenue_musd=('revenue_musd', 'mean'),
        mean_rating=('vote_average', 'mean'),
    ).sort_values('total_revenue_musd', ascending=False)


# Most Successful Directors
# Grouped by director, ranked by total revenue. Co-directed films group
# under their combined '|'-joined credit (see cleaning.get_directors),
# not split across two individual entries.

def most_successful_directors(df):
    return df.groupby('director').agg(
        n_movies=('title', 'count'),
        total_revenue_musd=('revenue_musd', 'sum'),
        mean_rating=('vote_average', 'mean'),
    ).sort_values('total_revenue_musd', ascending=False)
