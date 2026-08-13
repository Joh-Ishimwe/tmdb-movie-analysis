"""
Step 2: Data Cleaning and Preprocessing.

Pure DataFrame transforms -- no file paths, no network calls. Takes the
raw DataFrame (already including cast/crew, from fetch.py) and returns
the cleaned one. scripts/02_clean_data.py handles the file I/O.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

FINAL_COLUMNS = [
    'id', 'title', 'tagline', 'release_date', 'genres', 'belongs_to_collection',
    'original_language', 'budget_musd', 'revenue_musd', 'production_companies',
    'production_countries', 'vote_count', 'vote_average', 'popularity', 'runtime',
    'overview', 'spoken_languages', 'poster_path', 'cast', 'cast_size', 'director', 'crew_size'
]


def drop_irrelevant_columns(df):
    columns_to_drop = ['adult', 'imdb_id', 'original_title', 'video', 'homepage']
    df = df.drop(columns=columns_to_drop)

    # 'softcore' isn't in any official TMDb docs and is always False here.
    if 'softcore' in df.columns:
        df = df.drop(columns=['softcore'])

    logger.info("Columns remaining: %d", df.shape[1])
    return df


def extract_names(item_list):
    """Join each dict's 'name' with '|'. Used for genres,
    production_companies, production_countries, spoken_languages.

    Falls back to 'english_name' when 'name' is empty (e.g. Xhosa has no
    native-script name in TMDb) instead of dropping it or leaving a
    stray '|'."""
    if isinstance(item_list, list):
        return "|".join([item.get('name') or item.get('english_name') for item in item_list])
    return None


def extract_collection_name(collection):
    if isinstance(collection, dict):
        return collection.get('name')
    return None


def extract_json_columns(df):
    df['genres'] = df['genres'].apply(extract_names)
    df['production_companies'] = df['production_companies'].apply(extract_names)
    df['production_countries'] = df['production_countries'].apply(extract_names)
    df['spoken_languages'] = df['spoken_languages'].apply(extract_names)

    # belongs_to_collection is a single dict (or None), not a list --
    # handled with .get('name') so a missing key never raises an error.
    df['belongs_to_collection'] = df['belongs_to_collection'].apply(extract_collection_name)

    # origin_country is a plain list of country codes (no nested dicts).
    df['origin_country'] = df['origin_country'].apply(
        lambda c: "|".join(c) if isinstance(c, list) else c
    )

    return df


def inspect_extracted_columns(df):
    """Full value_counts() go to DEBUG (detailed, but noisy for a routine
    run); INFO gets one summary line with just the missing/empty counts."""
    extracted_cols = [
        'genres', 'belongs_to_collection', 'production_countries',
        'production_companies', 'spoken_languages'
    ]

    missing_counts = {}
    for col in extracted_cols:
        missing_counts[col] = int(df[col].isna().sum() + (df[col] == '').sum())
        logger.debug("--- %s ---\n%s", col, df[col].value_counts().head(10))

    logger.info("Inspected extracted columns, missing/empty: %s", missing_counts)


def convert_data_types(df):
    # errors='coerce' turns unparseable values into NaN/NaT instead of raising.
    df['budget'] = pd.to_numeric(df['budget'], errors='coerce')
    df['id'] = pd.to_numeric(df['id'], errors='coerce')
    df['popularity'] = pd.to_numeric(df['popularity'], errors='coerce')

    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    df['release_year'] = df['release_date'].dt.year

    return df


def fix_budget_revenue_runtime(df):
    # 0 isn't a plausible real value here -- it means missing data.
    df['budget'] = df['budget'].replace(0, np.nan)
    df['revenue'] = df['revenue'].replace(0, np.nan)
    df['runtime'] = df['runtime'].replace(0, np.nan)

    logger.info(
        "Missing budget: %d, revenue: %d, runtime: %d",
        df['budget'].isna().sum(), df['revenue'].isna().sum(), df['runtime'].isna().sum(),
    )

    df['budget_musd'] = df['budget'] / 1_000_000
    df['revenue_musd'] = df['revenue'] / 1_000_000

    return df


def fix_zero_vote_counts(df):
    # vote_count == 0 means vote_average has no real data behind it.
    zero_votes = df[df['vote_count'] == 0]
    logger.info("Movies with 0 vote_count: %d", len(zero_votes))

    df.loc[df['vote_count'] == 0, 'vote_average'] = np.nan
    return df


def fix_placeholder_text(df):
    logger.debug("overview value_counts:\n%s", df['overview'].value_counts().head(10))
    logger.debug("tagline value_counts:\n%s", df['tagline'].value_counts().head(10))

    overview_placeholders = (df['overview'] == 'No Data').sum()
    tagline_placeholders = (df['tagline'] == 'No Data').sum()

    df['overview'] = df['overview'].replace('No Data', np.nan)
    df['tagline'] = df['tagline'].replace('No Data', np.nan)

    logger.info(
        "Replaced placeholder text: %d overview, %d tagline",
        overview_placeholders, tagline_placeholders,
    )
    return df


def drop_duplicates_and_unknowns(df):
    # Exclude 'credits' (nested dicts aren't hashable/comparable); it's
    # dropped later anyway in add_cast_and_crew.
    is_duplicate = df.drop(columns='credits', errors='ignore').duplicated()

    logger.info(
        "Duplicate rows: %d, missing id: %d, missing title: %d",
        is_duplicate.sum(), df['id'].isna().sum(), df['title'].isna().sum(),
    )

    df = df[~is_duplicate]
    df = df.dropna(subset=['id', 'title'])
    return df


def drop_sparse_rows(df, min_non_null=10):
    non_null_counts = df.notna().sum(axis=1)
    df = df[non_null_counts >= min_non_null]
    logger.info("Rows remaining: %d", len(df))
    return df


def filter_released(df):
    logger.debug("status value_counts:\n%s", df['status'].value_counts())

    df = df[df['status'] == 'Released']
    df = df.drop(columns=['status'])

    logger.info("Filtered to 'Released': %d rows, %d columns remaining", len(df), df.shape[1])
    return df


# cast/director/crew come from df['credits'], bundled in by fetch.py via
# append_to_response=credits -- no separate call needed here.

def get_cast_string(credits, top_n=10):
    if not isinstance(credits, dict):
        return None
    cast_list = credits.get('cast', [])
    names = [person['name'] for person in cast_list[:top_n]]
    return "|".join(names) if names else None


def get_list_size(credits, key):
    """Reused for both cast_size (key='cast') and crew_size (key='crew')."""
    if not isinstance(credits, dict):
        return 0
    return len(credits.get(key, []))


def get_directors(credits):
    """Join every 'Director' crew credit with '|' (co-directed films have
    more than one). Sorted first so the same pair always joins the same
    way -- TMDb doesn't list them in a consistent order across films."""
    if not isinstance(credits, dict):
        return None
    crew_list = credits.get('crew', [])
    directors = sorted(person['name'] for person in crew_list if person.get('job') == 'Director')
    return "|".join(directors) if directors else None


def add_cast_and_crew(df):
    df['cast'] = df['credits'].apply(get_cast_string)
    df['cast_size'] = df['credits'].apply(lambda c: get_list_size(c, 'cast'))
    df['director'] = df['credits'].apply(get_directors)
    df['crew_size'] = df['credits'].apply(lambda c: get_list_size(c, 'crew'))

    return df.drop(columns=['credits'])


def finalize(df):
    df = df[FINAL_COLUMNS]
    df = df.reset_index(drop=True)
    return df


# Orchestrator -- chains every step above in order.

def clean_data(raw_df):
    df = drop_irrelevant_columns(raw_df)
    df = extract_json_columns(df)
    inspect_extracted_columns(df)

    df = convert_data_types(df)
    df = fix_budget_revenue_runtime(df)
    df = fix_zero_vote_counts(df)
    df = fix_placeholder_text(df)

    df = drop_duplicates_and_unknowns(df)
    df = drop_sparse_rows(df)
    df = filter_released(df)

    df = add_cast_and_crew(df)
    df = finalize(df)

    return df
