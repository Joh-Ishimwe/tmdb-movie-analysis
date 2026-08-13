"""Tests for scripts/02_clean_data.py -- pure DataFrame/dict transforms.

No network or disk access: these exercise the helper functions directly
with small, hand-built inputs.
"""

import numpy as np
import pandas as pd


# --- extract_names ----------------------------------------------------------

def test_extract_names_joins_names_with_pipe(clean_data):
    items = [{'name': 'Action'}, {'name': 'Comedy'}]
    assert clean_data.extract_names(items) == 'Action|Comedy'


def test_extract_names_non_list_returns_none(clean_data):
    assert clean_data.extract_names(None) is None
    assert clean_data.extract_names({'name': 'not a list'}) is None


def test_extract_names_empty_list_returns_empty_string(clean_data):
    assert clean_data.extract_names([]) == ''


def test_extract_names_falls_back_to_english_name_when_native_name_missing(clean_data):
    """Regression test for the real bug found in this dataset: TMDb has no
    native-script 'name' for some languages (e.g. Xhosa) -- only
    'english_name'. Falling back keeps the language instead of silently
    dropping it or leaving a stray '|' from an empty string."""
    items = [
        {'english_name': 'English', 'name': 'English'},
        {'english_name': 'Xhosa', 'name': ''},
    ]
    assert clean_data.extract_names(items) == 'English|Xhosa'


# --- extract_collection_name -------------------------------------------------

def test_extract_collection_name_from_dict(clean_data):
    collection = {'id': 1, 'name': 'X Collection'}
    assert clean_data.extract_collection_name(collection) == 'X Collection'


def test_extract_collection_name_none_when_not_a_dict(clean_data):
    assert clean_data.extract_collection_name(None) is None


# --- drop_irrelevant_columns --------------------------------------------------

def test_drop_irrelevant_columns_removes_expected_columns(clean_data):
    df = pd.DataFrame({
        'adult': [False], 'imdb_id': ['tt1'], 'original_title': ['x'],
        'video': [False], 'homepage': ['url'], 'softcore': [False],
        'title': ['Movie'], 'budget': [100],
    })
    result = clean_data.drop_irrelevant_columns(df)
    assert set(result.columns) == {'title', 'budget'}


def test_drop_irrelevant_columns_tolerates_missing_softcore(clean_data):
    df = pd.DataFrame({
        'adult': [False], 'imdb_id': ['tt1'], 'original_title': ['x'],
        'video': [False], 'homepage': ['url'], 'title': ['Movie'],
    })
    result = clean_data.drop_irrelevant_columns(df)
    assert list(result.columns) == ['title']


# --- convert_data_types -------------------------------------------------------

def test_convert_data_types_coerces_numeric_and_dates(clean_data):
    df = pd.DataFrame({
        'budget': ['100', 'not-a-number'],
        'id': ['1', '2'],
        'popularity': ['5.5', '6.6'],
        'release_date': ['2020-01-01', 'not-a-date'],
    })
    result = clean_data.convert_data_types(df)

    assert result['budget'].tolist()[0] == 100
    assert np.isnan(result['budget'].tolist()[1])
    assert result['release_year'].tolist()[0] == 2020
    assert pd.isna(result['release_date'].tolist()[1])


# --- fix_budget_revenue_runtime ------------------------------------------------

def test_fix_budget_revenue_runtime_treats_zero_as_missing(clean_data):
    df = pd.DataFrame({
        'budget': [0, 5_000_000],
        'revenue': [0, 20_000_000],
        'runtime': [0, 120],
    })
    result = clean_data.fix_budget_revenue_runtime(df)

    assert result['budget'].isna().sum() == 1
    assert result['revenue'].isna().sum() == 1
    assert result['runtime'].isna().sum() == 1
    assert result['budget_musd'].tolist()[1] == 5.0
    assert result['revenue_musd'].tolist()[1] == 20.0


# --- fix_zero_vote_counts -------------------------------------------------------

def test_fix_zero_vote_counts_blanks_rating_only_when_votes_are_zero(clean_data):
    df = pd.DataFrame({'vote_count': [0, 10], 'vote_average': [5.0, 7.5]})
    result = clean_data.fix_zero_vote_counts(df)

    assert pd.isna(result['vote_average'].tolist()[0])
    assert result['vote_average'].tolist()[1] == 7.5


# --- fix_placeholder_text --------------------------------------------------------

def test_fix_placeholder_text_replaces_no_data_with_nan(clean_data):
    df = pd.DataFrame({
        'overview': ['No Data', 'A real overview'],
        'tagline': ['No Data', 'A real tagline'],
    })
    result = clean_data.fix_placeholder_text(df)

    assert pd.isna(result['overview'].tolist()[0])
    assert result['overview'].tolist()[1] == 'A real overview'
    assert pd.isna(result['tagline'].tolist()[0])


# --- drop_duplicates_and_unknowns -------------------------------------------------

def test_drop_duplicates_and_unknowns_removes_dupes_and_missing_id_or_title(clean_data):
    df = pd.DataFrame({
        'id': [1, 1, 2, np.nan],
        'title': ['A', 'A', np.nan, 'D'],
    })
    result = clean_data.drop_duplicates_and_unknowns(df)

    # Row 0/1 duplicate -> one dropped; row with missing title dropped;
    # row with missing id dropped. Only the unique (1, 'A') row survives.
    assert len(result) == 1
    assert result.iloc[0]['id'] == 1
    assert result.iloc[0]['title'] == 'A'


# --- drop_sparse_rows -------------------------------------------------------------

def test_drop_sparse_rows_keeps_rows_at_or_above_threshold(clean_data):
    # 3 columns: a row with all 3 filled (3 non-null) survives at min=3,
    # a row with only 2 filled does not.
    df = pd.DataFrame({
        'a': [1, 1],
        'b': [2, 2],
        'c': [3, np.nan],
    })
    result = clean_data.drop_sparse_rows(df, min_non_null=3)
    assert len(result) == 1


# --- filter_released ---------------------------------------------------------------

def test_filter_released_keeps_only_released_and_drops_status_column(clean_data):
    df = pd.DataFrame({
        'title': ['A', 'B', 'C'],
        'status': ['Released', 'Rumored', 'Released'],
    })
    result = clean_data.filter_released(df)

    assert 'status' not in result.columns
    assert result['title'].tolist() == ['A', 'C']


# --- credits helpers ---------------------------------------------------------------

def test_get_cast_string_takes_top_n_names(clean_data):
    credits = {'cast': [{'name': 'A'}, {'name': 'B'}, {'name': 'C'}]}
    assert clean_data.get_cast_string(credits, top_n=2) == 'A|B'


def test_get_cast_string_empty_cast_returns_none(clean_data):
    assert clean_data.get_cast_string({'cast': []}) is None


def test_get_list_size_counts_cast_and_crew(clean_data):
    credits = {'cast': [{'name': 'A'}], 'crew': [{'name': 'B'}, {'name': 'C'}]}
    assert clean_data.get_list_size(credits, 'cast') == 1
    assert clean_data.get_list_size(credits, 'crew') == 2


def test_get_list_size_missing_key_is_zero(clean_data):
    assert clean_data.get_list_size({}, 'cast') == 0


def test_get_director_finds_crew_member_with_director_job(clean_data):
    credits = {'crew': [{'name': 'Editor Ed', 'job': 'Editor'}, {'name': 'Dir Dan', 'job': 'Director'}]}
    assert clean_data.get_director(credits) == 'Dir Dan'


def test_get_director_returns_none_when_no_director_listed(clean_data):
    credits = {'crew': [{'name': 'Editor Ed', 'job': 'Editor'}]}
    assert clean_data.get_director(credits) is None


def test_get_director_returns_first_listed_when_co_directed(clean_data):
    """Known limitation, pinned rather than silently left undocumented:
    for a co-directed film TMDb lists multiple crew members with
    job='Director' (e.g. the real Endgame/Infinity War data has both
    Russo brothers), and this takes only the first one in API order."""
    credits = {'crew': [{'name': 'Anthony Russo', 'job': 'Director'},
                         {'name': 'Joe Russo', 'job': 'Director'}]}
    assert clean_data.get_director(credits) == 'Anthony Russo'


# --- credits helpers are defensive against a missing/malformed credits dict ---
# (a row's 'credits' value should always be a dict once append_to_response=
# credits is used, but these guard against unexpected shapes rather than
# raising deep inside a .apply() call)

def test_get_cast_string_non_dict_returns_none(clean_data):
    assert clean_data.get_cast_string(None) is None
    assert clean_data.get_cast_string(float('nan')) is None


def test_get_list_size_non_dict_returns_zero(clean_data):
    assert clean_data.get_list_size(None, 'cast') == 0


def test_get_director_non_dict_returns_none(clean_data):
    assert clean_data.get_director(None) is None


# --- add_cast_and_crew reads from an already-embedded 'credits' column ------

def test_add_cast_and_crew_extracts_from_credits_column_and_drops_it(clean_data):
    df = pd.DataFrame({
        'id': [1, 2],
        'credits': [
            {'cast': [{'name': 'Actor A'}], 'crew': [{'name': 'Dir A', 'job': 'Director'}]},
            {'cast': [], 'crew': []},
        ],
    })

    result = clean_data.add_cast_and_crew(df)

    assert 'credits' not in result.columns
    assert result.loc[0, 'cast'] == 'Actor A'
    assert result.loc[0, 'director'] == 'Dir A'
    assert result.loc[0, 'cast_size'] == 1
    assert pd.isna(result.loc[1, 'cast'])
    assert pd.isna(result.loc[1, 'director'])
    assert result.loc[1, 'crew_size'] == 0


# --- finalize ---------------------------------------------------------------------

def test_finalize_reorders_columns_and_resets_index(clean_data):
    cols = clean_data.FINAL_COLUMNS
    df = pd.DataFrame({col: [0, 1, 2] for col in reversed(cols)}, index=[10, 20, 30])

    result = clean_data.finalize(df)

    assert list(result.columns) == cols
    assert result.index.tolist() == [0, 1, 2]
