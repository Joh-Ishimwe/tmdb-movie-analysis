"""
Step 1: Fetch Movie Data from API.

Thin wrapper: checks the cache, calls tmdb_pipeline.fetch, saves the result.
"""

import json
from pathlib import Path

from tmdb_pipeline.api import load_credentials
from tmdb_pipeline.cli import ensure_dir, force_utf8_stdout
from tmdb_pipeline.fetch import MOVIE_IDS, dataset_exists_and_is_valid, download_movies

force_utf8_stdout()


OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "movies.json"


def save_movies(movies, output_file):
    ensure_dir(output_file.parent)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(movies, file, indent=2, ensure_ascii=False)

    print(f"Dataset saved to: {output_file}")


def main():
    if dataset_exists_and_is_valid(OUTPUT_FILE):
        print(f"Dataset already exists at: {OUTPUT_FILE}")
        print("Skipping API download.")
        return

    api_key, movie_url = load_credentials()
    movies = download_movies(MOVIE_IDS, api_key, movie_url)
    save_movies(movies, OUTPUT_FILE)


if __name__ == "__main__":
    main()
