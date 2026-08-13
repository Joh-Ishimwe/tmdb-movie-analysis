"""
Step 1: Fetch Movie Data from API.

Thin wrapper: checks the cache, calls tmdb_pipeline.fetch, saves the result.
"""

import json
import logging

from tmdb_pipeline.api import load_credentials
from tmdb_pipeline.cli import PROJECT_ROOT, ensure_dir, force_utf8_stdout
from tmdb_pipeline.fetch import MOVIE_IDS, dataset_exists_and_is_valid, download_movies
from tmdb_pipeline.logging_config import setup_logging

force_utf8_stdout()

# Named explicitly rather than via __name__: __name__ would be
# "01_fetch_raw_data" when exec'd by run_pipeline.py (its only caller),
# but naming it explicitly here keeps this consistent with the other stages.
logger = logging.getLogger("01_fetch_raw_data")


OUTPUT_DIR = PROJECT_ROOT / "data/raw"
OUTPUT_FILE = OUTPUT_DIR / "movies.json"


def save_movies(movies, output_file):
    ensure_dir(output_file.parent)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(movies, file, indent=2, ensure_ascii=False)

    logger.info("Dataset saved to: %s", output_file)


def run():
    setup_logging()

    if dataset_exists_and_is_valid(OUTPUT_FILE):
        logger.info("Dataset already exists at: %s", OUTPUT_FILE)
        logger.info("Skipping API download.")
        return

    try:
        api_key, movie_url = load_credentials()
        movies = download_movies(MOVIE_IDS, api_key, movie_url)
        save_movies(movies, OUTPUT_FILE)
    except Exception:
        logger.exception("Step 1 (fetch) failed.")
        raise
