"""
Step 2: Data Cleaning and Preprocessing.

Thin CLI wrapper around tmdb_pipeline.cleaning: handles file I/O (reading
the raw dataset, saving the cleaned one). All the actual cleaning logic
lives in tmdb_pipeline/cleaning.py, so it's directly importable and
testable without going through this script. Makes no network calls
itself, so it needs no .env credentials to run.
"""

import json
import sys
from pathlib import Path

import pandas as pd

from tmdb_pipeline.cleaning import clean_data

# Windows terminals default to cp1252, which can't print some movie titles/
# language names (accented characters, etc.). Force UTF-8 so this script
# doesn't crash on print() the way Jupyter (UTF-8 by default) never does.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


RAW_FILE = Path("data/raw/movies.json")
PROCESSED_DIR = Path("data/processed")
PROCESSED_FILE = PROCESSED_DIR / "tmdb_movies_clean.csv"


def load_raw_data(path):
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run 01_fetch_raw_data.py first.")

    with open(path, "r", encoding="utf-8") as file:
        movies_data = json.load(file)

    print(f"Loaded {len(movies_data)} movies from {path}")
    return pd.DataFrame(movies_data)


def main():
    raw_df = load_raw_data(RAW_FILE)
    df = clean_data(raw_df)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_FILE, index=False)

    print()
    print(f"Saved {len(df)} rows to {PROCESSED_FILE}")


if __name__ == "__main__":
    main()
