"""
Step 2: Data Cleaning and Preprocessing.

Pure DataFrame transforms -- no file paths, no network calls. Takes the
raw DataFrame (as loaded from 01_fetch_raw_data.py's output, already
including cast/crew via append_to_response=credits) and returns the
cleaned one. scripts/02_clean_data.py handles reading/writing files;
this module is what's actually reusable and testable.
"""

import numpy as np
import pandas as pd

# Reorder columns & reset index (Step 2's final shape)
FINAL_COLUMNS = [
    'id', 'title', 'tagline', 'release_date', 'genres', 'belongs_to_collection',
    'original_language', 'budget_musd', 'revenue_musd', 'production_companies',
    'production_countries', 'vote_count', 'vote_average', 'popularity', 'runtime',
    'overview', 'spoken_languages', 'poster_path', 'cast', 'cast_size', 'director', 'crew_size'
]


# Drop irrelevant / undocumented columns

def drop_irrelevant_columns(df):
    columns_to_drop = ['adult', 'imdb_id', 'original_title', 'video', 'homepage']
    df = df.drop(columns=columns_to_drop)

    # 'softcore' is an undocumented boolean flag -- not in any official
    # TMDb docs, and always False in this dataset. Irrelevant, drop it too.
    if 'softcore' in df.columns:
        df = df.drop(columns=['softcore'])

    print(f"Columns remaining: {df.shape[1]}")
    return df


# Extract JSON-nested columns into clean, readable strings

def extract_names(item_list):
    """Join the 'name' field of each dict in a list of dicts with '|'.
    Reused for genres, production_companies, production_countries, and
    spoken_languages -- they're all shaped the same way.

    Some TMDb languages (e.g. Xhosa) have no native-script 'name' -- only
    'english_name'. Falling back keeps the language instead of silently
    dropping it or leaving a stray '|' from an empty string."""
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


# Inspect extracted columns for anomalies

def inspect_extracted_columns(df):
    extracted_cols = [
        'genres', 'belongs_to_collection', 'production_countries',
        'production_companies', 'spoken_languages'
    ]

    for col in extracted_cols:
        print(f"--- {col} ---")
        print(f"Missing/empty: {df[col].isna().sum() + (df[col] == '').sum()}")
        print(df[col].value_counts().head(10))
        print()


# Convert data types
# errors='coerce' converts unparseable values to NaN/NaT instead of crashing.

def convert_data_types(df):
    df['budget'] = pd.to_numeric(df['budget'], errors='coerce')
    df['id'] = pd.to_numeric(df['id'], errors='coerce')
    df['popularity'] = pd.to_numeric(df['popularity'], errors='coerce')

    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    df['release_year'] = df['release_date'].dt.year

    return df


# Replace unrealistic zero values & convert to million USD
# A budget/revenue/runtime of exactly 0 is not physically plausible for a
# real released movie -- it signals missing data, not a true value of zero.

def fix_budget_revenue_runtime(df):
    df['budget'] = df['budget'].replace(0, np.nan)
    df['revenue'] = df['revenue'].replace(0, np.nan)
    df['runtime'] = df['runtime'].replace(0, np.nan)

    print("Missing budget:", df['budget'].isna().sum())
    print("Missing revenue:", df['revenue'].isna().sum())
    print("Missing runtime:", df['runtime'].isna().sum())

    df['budget_musd'] = df['budget'] / 1_000_000
    df['revenue_musd'] = df['revenue'] / 1_000_000

    return df


# Treat vote_average as missing when vote_count is 0
# If vote_count is 0, vote_average has no real data behind it.

def fix_zero_vote_counts(df):
    zero_votes = df[df['vote_count'] == 0]
    print(f"Movies with 0 vote_count: {len(zero_votes)}")

    df.loc[df['vote_count'] == 0, 'vote_average'] = np.nan
    return df


# Replace placeholder text in overview / tagline

def fix_placeholder_text(df):
    print(df['overview'].value_counts().head(10))
    print(df['tagline'].value_counts().head(10))

    df['overview'] = df['overview'].replace('No Data', np.nan)
    df['tagline'] = df['tagline'].replace('No Data', np.nan)
    return df


# Remove duplicates and rows with unknown id / title

def drop_duplicates_and_unknowns(df):
    # 'credits' holds nested dicts, which pandas can't hash to compare --
    # exclude it from the duplicate check (it's dropped later anyway, in
    # add_cast_and_crew). id/title alone are enough to define a duplicate
    # movie record.
    is_duplicate = df.drop(columns='credits', errors='ignore').duplicated()

    print("Duplicate rows:", is_duplicate.sum())
    print("Missing id:", df['id'].isna().sum())
    print("Missing title:", df['title'].isna().sum())

    df = df[~is_duplicate]
    df = df.dropna(subset=['id', 'title'])
    return df


# Keep only rows with at least 10 non-NaN columns

def drop_sparse_rows(df, min_non_null=10):
    non_null_counts = df.notna().sum(axis=1)
    df = df[non_null_counts >= min_non_null]
    print(f"Rows remaining: {len(df)}")
    return df


# Filter to 'Released' movies only, then drop status

def filter_released(df):
    print(df['status'].value_counts())

    df = df[df['status'] == 'Released']
    df = df.drop(columns=['status'])

    print(f"Rows remaining: {len(df)}")
    print(f"Columns remaining: {df.shape[1]}")
    return df


# Extract cast & crew
# cast, cast_size, director, and crew_size aren't in the base /movie/{id}
# response, but fetch.py requests them with append_to_response=credits,
# so they arrive bundled under df['credits'] -- no separate
# /movie/{id}/credits call needed per movie here.

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
    """Join every crew member credited as 'Director' with '|', same
    convention as cast/genres/production_companies. Co-directed films are
    common (e.g. this dataset's Avengers: Endgame/Infinity War -- both
    Russo brothers -- and Frozen/Frozen II -- Jennifer Lee & Chris Buck):
    taking only the first Director credit would silently drop a real
    co-director and misattribute the film to one person, with the actual
    name picked depending on unstable API list order.

    Sorted before joining for a second reason: TMDb doesn't list the same
    co-directing pair in the same order on every film (Endgame lists
    Anthony Russo first, Infinity War lists Joe Russo first, for the
    exact same two people) -- without sorting, groupby('director') in the
    KPI step would split one directing team into two different groups."""
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
