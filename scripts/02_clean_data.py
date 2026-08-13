"""
Step 2: Data Cleaning and Preprocessing

Loads the raw TMDb dataset produced by 01_fetch_raw_data.py, cleans and
transforms it, enriches it with cast/crew data from the /credits endpoint,
and saves the result to data/processed/tmdb_movies_clean.csv so Step 3
(KPI analysis) can load it directly without re-fetching from the API.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from tmdb_api import load_credentials, fetch_json

# Windows terminals default to cp1252, which can't print some movie titles/
# language names (accented characters, etc.). Force UTF-8 so this script
# doesn't crash on print() the way Jupyter (UTF-8 by default) never does.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# 1. Load environment variables

API_KEY, MOVIE_URL = load_credentials()


# 2. File locations

RAW_FILE = Path("data/raw/movies.json")
PROCESSED_DIR = Path("data/processed")
PROCESSED_FILE = PROCESSED_DIR / "tmdb_movies_clean.csv"


# 3. Load the raw dataset

def load_raw_data():
    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"{RAW_FILE} not found. Run 01_fetch_raw_data.py first."
        )

    with open(RAW_FILE, "r", encoding="utf-8") as file:
        movies_data = json.load(file)

    print(f"Loaded {len(movies_data)} movies from {RAW_FILE}")
    return pd.DataFrame(movies_data)


# 4. Drop irrelevant / undocumented columns

def drop_irrelevant_columns(df):
    columns_to_drop = ['adult', 'imdb_id', 'original_title', 'video', 'homepage']
    df = df.drop(columns=columns_to_drop)

    # 'softcore' is an undocumented boolean flag -- not in any official
    # TMDb docs, and always False in this dataset. Irrelevant, drop it too.
    if 'softcore' in df.columns:
        df = df.drop(columns=['softcore'])

    print(f"Columns remaining: {df.shape[1]}")
    return df


# 5. Extract JSON-nested columns into clean, readable strings

def extract_names(item_list):
    """Join the 'name' field of each dict in a list of dicts with '|'.
    Reused for genres, production_companies, production_countries, and
    spoken_languages -- they're all shaped the same way."""
    if isinstance(item_list, list):
        return "|".join([item['name'] for item in item_list])
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


# 6. Inspect extracted columns for anomalies

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


# 7. Convert data types
# errors='coerce' converts unparseable values to NaN/NaT instead of crashing.

def convert_data_types(df):
    df['budget'] = pd.to_numeric(df['budget'], errors='coerce')
    df['id'] = pd.to_numeric(df['id'], errors='coerce')
    df['popularity'] = pd.to_numeric(df['popularity'], errors='coerce')

    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    df['release_year'] = df['release_date'].dt.year

    return df


# 8. Replace unrealistic zero values & convert to million USD
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


# 9. Treat vote_average as missing when vote_count is 0
# If vote_count is 0, vote_average has no real data behind it.

def fix_zero_vote_counts(df):
    zero_votes = df[df['vote_count'] == 0]
    print(f"Movies with 0 vote_count: {len(zero_votes)}")

    df.loc[df['vote_count'] == 0, 'vote_average'] = np.nan
    return df


# 10. Replace placeholder text in overview / tagline

def fix_placeholder_text(df):
    print(df['overview'].value_counts().head(10))
    print(df['tagline'].value_counts().head(10))

    df['overview'] = df['overview'].replace('No Data', np.nan)
    df['tagline'] = df['tagline'].replace('No Data', np.nan)
    return df


# 11. Remove duplicates and rows with unknown id / title

def drop_duplicates_and_unknowns(df):
    print("Duplicate rows:", df.duplicated().sum())
    print("Missing id:", df['id'].isna().sum())
    print("Missing title:", df['title'].isna().sum())

    df = df.drop_duplicates()
    df = df.dropna(subset=['id', 'title'])
    return df


# 12. Keep only rows with at least 10 non-NaN columns

def drop_sparse_rows(df, min_non_null=10):
    non_null_counts = df.notna().sum(axis=1)
    df = df[non_null_counts >= min_non_null]
    print(f"Rows remaining: {len(df)}")
    return df


# 13. Filter to 'Released' movies only, then drop status

def filter_released(df):
    print(df['status'].value_counts())

    df = df[df['status'] == 'Released']
    df = df.drop(columns=['status'])

    print(f"Rows remaining: {len(df)}")
    print(f"Columns remaining: {df.shape[1]}")
    return df


# 14. Fetch cast & crew (credits endpoint)
# cast, cast_size, director, and crew_size don't exist in the /movie/{id}
# response -- they come from a separate endpoint: /movie/{id}/credits.

def fetch_credits(movie_ids):
    credits_data = {}
    failed_credit_ids = []

    for mid in movie_ids:
        url = f"{MOVIE_URL}{mid}/credits"
        try:
            credits_data[mid] = fetch_json(url, API_KEY, extra_params={"language": "en-US"})
        except requests.exceptions.RequestException as error:
            print(f"Failed to fetch credits for movie_id {mid}: {error}")
            failed_credit_ids.append(mid)

    print(f"Successfully fetched credits for {len(credits_data)} out of {len(movie_ids)} movies.")
    return credits_data


def get_cast_string(credits, top_n=10):
    cast_list = credits.get('cast', [])
    names = [person['name'] for person in cast_list[:top_n]]
    return "|".join(names) if names else None


def get_list_size(credits, key):
    """Reused for both cast_size (key='cast') and crew_size (key='crew')."""
    return len(credits.get(key, []))


def get_director(credits):
    crew_list = credits.get('crew', [])
    for person in crew_list:
        if person.get('job') == 'Director':
            return person['name']
    return None


def map_credits_field(df, credits_data, extractor):
    """Look up each row's credits (by movie id) and apply extractor to it,
    or None if that movie's credits failed to fetch."""
    return df['id'].map(lambda mid: extractor(credits_data[mid]) if mid in credits_data else None)


def add_cast_and_crew(df):
    credits_data = fetch_credits(df['id'])

    df['cast'] = map_credits_field(df, credits_data, get_cast_string)
    df['cast_size'] = map_credits_field(df, credits_data, lambda c: get_list_size(c, 'cast'))
    df['director'] = map_credits_field(df, credits_data, get_director)
    df['crew_size'] = map_credits_field(df, credits_data, lambda c: get_list_size(c, 'crew'))

    return df


# 15. Reorder columns & reset index

FINAL_COLUMNS = [
    'id', 'title', 'tagline', 'release_date', 'genres', 'belongs_to_collection',
    'original_language', 'budget_musd', 'revenue_musd', 'production_companies',
    'production_countries', 'vote_count', 'vote_average', 'popularity', 'runtime',
    'overview', 'spoken_languages', 'poster_path', 'cast', 'cast_size', 'director', 'crew_size'
]


def finalize(df):
    df = df[FINAL_COLUMNS]
    df = df.reset_index(drop=True)
    return df


# 16. Main pipeline

def clean_data():
    df = load_raw_data()

    df = drop_irrelevant_columns(df)
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

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_FILE, index=False)

    print()
    print(f"Saved {len(df)} rows to {PROCESSED_FILE}")

    return df


def main():
    clean_data()


if __name__ == "__main__":
    main()
