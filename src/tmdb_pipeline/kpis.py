"""
Step 3: KPI Implementation & Analysis.

Pure functions, no printing -- take a DataFrame, return a DataFrame.
Makes these directly unit-testable; scripts/03_kpis.py handles printing.
"""


def top_movies(dataframe, column, n=5, ascending=False, min_budget=None):
    """
    Top (or bottom) n movies ranked by column. One function for every
    ranking KPI (revenue, budget, profit, ROI, votes, rating, popularity).

    ascending  : False = highest first, True = lowest first
    min_budget : optional filter, e.g. only budget >= 10 (million)
    """
    data = dataframe.copy()

    if min_budget is not None:
        data = data[data['budget_musd'] >= min_budget]

    return data.sort_values(column, ascending=ascending).head(n)[['title', column]]


def add_profit_and_roi(df):
    df['profit_musd'] = df['revenue_musd'] - df['budget_musd']
    df['roi'] = df['revenue_musd'] / df['budget_musd']
    return df


def search_scifi_action_with_actor(df, actor_name):
    """Best-rated Sci-Fi Action movies starring actor_name, highest
    rating first."""
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


def franchise_vs_standalone_performance(df):
    """A movie counts as a franchise entry if belongs_to_collection is set."""
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


def most_successful_franchises(df):
    """Grouped by belongs_to_collection, ranked by total revenue."""
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


def most_successful_directors(df):
    """Grouped by director, ranked by total revenue. Co-directors group
    under one combined credit (see cleaning.get_directors)."""
    return df.groupby('director').agg(
        n_movies=('title', 'count'),
        total_revenue_musd=('revenue_musd', 'sum'),
        mean_rating=('vote_average', 'mean'),
    ).sort_values('total_revenue_musd', ascending=False)
