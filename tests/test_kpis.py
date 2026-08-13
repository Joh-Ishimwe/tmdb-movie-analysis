"""Tests for tmdb_pipeline.kpis -- the ranking UDF and groupby aggregations.

top_movies() is reused for every single KPI ranking (revenue, budget,
profit, ROI, votes, rating, popularity) -- a bug here would silently break
8+ KPIs at once, so it gets the most thorough coverage.
"""

import pandas as pd
import pytest

from tmdb_pipeline.kpis import (
    add_profit_and_roi,
    franchise_vs_standalone_performance,
    most_successful_directors,
    most_successful_franchises,
    search_by_cast_and_director,
    search_scifi_action_with_actor,
    top_movies,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        'id': [1, 2, 3, 4],
        'title': ['Alpha', 'Beta', 'Gamma', 'Delta'],
        'budget_musd': [100.0, 5.0, 50.0, 20.0],
        'revenue_musd': [400.0, 50.0, 500.0, 40.0],
        'vote_count': [1000, 5, 200, 300],
        'vote_average': [7.5, 9.0, 4.0, 6.0],
        'popularity': [50.0, 5.0, 20.0, 10.0],
        'belongs_to_collection': ['X Collection', None, 'X Collection', None],
        'director': ['Dir A', 'Dir B', 'Dir A', 'Dir C'],
        'genres': ['Science Fiction|Action', 'Drama', 'Action', 'Comedy'],
        'cast': ['Star One|Star Two', 'Star Three', 'Star One', 'Star Four'],
        'runtime': [120, 90, 150, 100],
    })


# --- top_movies --------------------------------------------------------------

def test_top_movies_orders_descending_by_default(sample_df):
    result = top_movies(sample_df, 'revenue_musd', n=2)
    assert result['title'].tolist() == ['Gamma', 'Alpha']


def test_top_movies_ascending_flips_order(sample_df):
    result = top_movies(sample_df, 'revenue_musd', n=2, ascending=True)
    assert result['title'].tolist() == ['Delta', 'Beta']


def test_top_movies_min_budget_filters_before_ranking(sample_df):
    # Beta (budget 5) would otherwise place well, but min_budget=10 must
    # exclude it before ranking, not just filter the final result.
    result = top_movies(sample_df, 'revenue_musd', n=4, min_budget=10)
    assert 'Beta' not in result['title'].tolist()
    assert set(result['title']) == {'Alpha', 'Gamma', 'Delta'}


def test_top_movies_returns_only_title_and_ranked_column(sample_df):
    result = top_movies(sample_df, 'popularity', n=1)
    assert list(result.columns) == ['title', 'popularity']


def test_top_movies_n_truncates_results(sample_df):
    result = top_movies(sample_df, 'revenue_musd', n=1)
    assert len(result) == 1


# --- add_profit_and_roi -------------------------------------------------------

def test_add_profit_and_roi_computes_expected_values(sample_df):
    result = add_profit_and_roi(sample_df.copy())
    row = result[result['title'] == 'Alpha'].iloc[0]
    assert row['profit_musd'] == 300.0
    assert row['roi'] == 4.0


# --- search_scifi_action_with_actor -------------------------------------------

def test_search_scifi_action_with_actor_matches_genre_and_cast(sample_df):
    result = search_scifi_action_with_actor(sample_df, 'Star One')
    assert result['title'].tolist() == ['Alpha']


def test_search_scifi_action_with_actor_no_match_returns_empty(sample_df):
    result = search_scifi_action_with_actor(sample_df, 'Nobody')
    assert len(result) == 0


def test_search_scifi_action_with_actor_sorts_by_rating_desc():
    df = pd.DataFrame({
        'title': ['Low', 'High'],
        'genres': ['Science Fiction|Action', 'Science Fiction|Action'],
        'cast': ['Star One', 'Star One'],
        'vote_average': [5.0, 9.0],
    })
    result = search_scifi_action_with_actor(df, 'Star One')
    assert result['title'].tolist() == ['High', 'Low']


# --- search_by_cast_and_director ------------------------------------------------

def test_search_by_cast_and_director_matches_both_criteria(sample_df):
    result = search_by_cast_and_director(sample_df, 'Star One', 'Dir A')
    assert set(result['title']) == {'Alpha', 'Gamma'}


def test_search_by_cast_and_director_sorts_by_runtime_ascending(sample_df):
    result = search_by_cast_and_director(sample_df, 'Star One', 'Dir A')
    # Alpha (120) shorter than Gamma (150)
    assert result['title'].tolist() == ['Alpha', 'Gamma']


def test_search_by_cast_and_director_no_match_returns_empty(sample_df):
    result = search_by_cast_and_director(sample_df, 'Star One', 'Dir B')
    assert len(result) == 0


# --- franchise_vs_standalone_performance --------------------------------------

def test_franchise_vs_standalone_performance_splits_correctly(sample_df):
    df = add_profit_and_roi(sample_df.copy())
    result = franchise_vs_standalone_performance(df)

    assert set(result.index) == {'Franchise', 'Standalone'}
    assert result.loc['Franchise', 'n_movies'] == 2
    assert result.loc['Standalone', 'n_movies'] == 2
    # Franchise = Alpha (400) + Gamma (500) -> mean 450
    assert result.loc['Franchise', 'mean_revenue_musd'] == 450.0
    # Standalone = Beta (50) + Delta (40) -> mean 45
    assert result.loc['Standalone', 'mean_revenue_musd'] == 45.0


# --- most_successful_franchises ------------------------------------------------

def test_most_successful_franchises_aggregates_and_sorts_by_revenue(sample_df):
    result = most_successful_franchises(sample_df)

    assert list(result.index) == ['X Collection']
    assert result.loc['X Collection', 'n_movies'] == 2
    assert result.loc['X Collection', 'total_revenue_musd'] == 900.0


# --- most_successful_directors --------------------------------------------------

def test_most_successful_directors_sorts_by_total_revenue_desc(sample_df):
    result = most_successful_directors(sample_df)

    # Dir A: Alpha(400) + Gamma(500) = 900 -- the clear top director.
    assert result.index.tolist()[0] == 'Dir A'
    assert result.loc['Dir A', 'total_revenue_musd'] == 900.0
    assert result.loc['Dir A', 'n_movies'] == 2
