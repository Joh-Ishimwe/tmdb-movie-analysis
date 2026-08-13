"""Tests for scripts/03_kpis.py -- the ranking UDF and groupby aggregations.

top_movies() is reused for every single KPI ranking (revenue, budget,
profit, ROI, votes, rating, popularity) -- a bug here would silently break
8+ KPIs at once, so it gets the most thorough coverage.
"""

import pandas as pd
import pytest


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
    })


# --- top_movies --------------------------------------------------------------

def test_top_movies_orders_descending_by_default(kpis, sample_df):
    result = kpis.top_movies(sample_df, 'revenue_musd', n=2)
    assert result['title'].tolist() == ['Gamma', 'Alpha']


def test_top_movies_ascending_flips_order(kpis, sample_df):
    result = kpis.top_movies(sample_df, 'revenue_musd', n=2, ascending=True)
    assert result['title'].tolist() == ['Delta', 'Beta']


def test_top_movies_min_budget_filters_before_ranking(kpis, sample_df):
    # Beta (budget 5) would otherwise place well, but min_budget=10 must
    # exclude it before ranking, not just filter the final result.
    result = kpis.top_movies(sample_df, 'revenue_musd', n=4, min_budget=10)
    assert 'Beta' not in result['title'].tolist()
    assert set(result['title']) == {'Alpha', 'Gamma', 'Delta'}


def test_top_movies_returns_only_title_and_ranked_column(kpis, sample_df):
    result = kpis.top_movies(sample_df, 'popularity', n=1)
    assert list(result.columns) == ['title', 'popularity']


def test_top_movies_n_truncates_results(kpis, sample_df):
    result = kpis.top_movies(sample_df, 'revenue_musd', n=1)
    assert len(result) == 1


# --- add_profit_and_roi -------------------------------------------------------

def test_add_profit_and_roi_computes_expected_values(kpis, sample_df):
    result = kpis.add_profit_and_roi(sample_df.copy())
    row = result[result['title'] == 'Alpha'].iloc[0]
    assert row['profit_musd'] == 300.0
    assert row['roi'] == 4.0


# --- franchise_vs_standalone_performance --------------------------------------

def test_franchise_vs_standalone_performance_splits_correctly(kpis, sample_df):
    df = kpis.add_profit_and_roi(sample_df.copy())
    result = kpis.franchise_vs_standalone_performance(df)

    assert set(result.index) == {'Franchise', 'Standalone'}
    assert result.loc['Franchise', 'n_movies'] == 2
    assert result.loc['Standalone', 'n_movies'] == 2
    # Franchise = Alpha (400) + Gamma (500) -> mean 450
    assert result.loc['Franchise', 'mean_revenue_musd'] == 450.0
    # Standalone = Beta (50) + Delta (40) -> mean 45
    assert result.loc['Standalone', 'mean_revenue_musd'] == 45.0


# --- most_successful_franchises ------------------------------------------------

def test_most_successful_franchises_aggregates_and_sorts_by_revenue(kpis, sample_df):
    result = kpis.most_successful_franchises(sample_df)

    assert list(result.index) == ['X Collection']
    assert result.loc['X Collection', 'n_movies'] == 2
    assert result.loc['X Collection', 'total_revenue_musd'] == 900.0


# --- most_successful_directors --------------------------------------------------

def test_most_successful_directors_sorts_by_total_revenue_desc(kpis, sample_df):
    result = kpis.most_successful_directors(sample_df)

    # Dir A: Alpha(400) + Gamma(500) = 900 -- the clear top director.
    assert result.index.tolist()[0] == 'Dir A'
    assert result.loc['Dir A', 'total_revenue_musd'] == 900.0
    assert result.loc['Dir A', 'n_movies'] == 2
