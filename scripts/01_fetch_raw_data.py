"""
Step 1: Fetch Movie Data from API.

Thin CLI wrapper around tmdb_pipeline.fetch: handles file I/O (checking
for a cached dataset, saving the result) and credential loading. All the
actual fetch/validate logic lives in tmdb_pipeline/fetch.py, so it's
directly importable and testable without going through this script.
"""

import json
import sys
from pathlib import Path

from tmdb_pipeline.api import load_credentials
from tmdb_pipeline.fetch import MOVIE_IDS, dataset_exists_and_is_valid, download_movies

# Windows terminals default to cp1252, which can't print some movie titles/
# language names (accented characters, etc.). Force UTF-8 so this script
# doesn't crash on print() the way Jupyter (UTF-8 by default) never does.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "movies.json"


def save_movies(movies, output_file):
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(movies, file, indent=2, ensure_ascii=False)

    print(f"Dataset saved to: {output_file}")


def main():
    # If a valid dataset already exists, don't call the API again.
    if dataset_exists_and_is_valid(OUTPUT_FILE):
        print(f"Dataset already exists at: {OUTPUT_FILE}")
        print("Skipping API download.")
        return

    api_key, movie_url = load_credentials()
    movies = download_movies(MOVIE_IDS, api_key, movie_url)
    save_movies(movies, OUTPUT_FILE)


if __name__ == "__main__":
    main()
