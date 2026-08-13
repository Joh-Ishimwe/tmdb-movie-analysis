"""
Step 1: Fetch Movie Data from API.

Thin wrapper: loads whatever's already cached, downloads only the IDs
still missing (e.g. after MOVIE_IDS changes), and saves the merged result.
"""

import json
import logging

from tmdb_pipeline.api import load_credentials
from tmdb_pipeline.cli import PROJECT_ROOT, ensure_dir, force_utf8_stdout
from tmdb_pipeline.fetch import MOVIE_IDS, download_movies, load_existing_movies
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

    try:
        existing_movies = load_existing_movies(OUTPUT_FILE)
        api_key, movie_url = load_credentials()
        new_movies = download_movies(MOVIE_IDS, api_key, movie_url, existing_movies)

        if new_movies:
            save_movies(existing_movies + new_movies, OUTPUT_FILE)
        else:
            logger.info("Dataset already up to date at: %s", OUTPUT_FILE)
    except Exception:
        logger.exception("Step 1 (fetch) failed.")
        raise
