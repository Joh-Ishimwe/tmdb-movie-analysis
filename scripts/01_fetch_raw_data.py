"""
Step 1: Fetch Movie Data from API.

Thin wrapper: checks the cache, calls tmdb_pipeline.fetch, saves the result.
"""

import json
import logging
from pathlib import Path

from tmdb_pipeline.api import load_credentials
from tmdb_pipeline.cli import ensure_dir, force_utf8_stdout
from tmdb_pipeline.fetch import MOVIE_IDS, dataset_exists_and_is_valid, download_movies
from tmdb_pipeline.logging_config import setup_logging

force_utf8_stdout()

# Named explicitly rather than via __name__: this script is only ever
# run as a top-level script (directly, or exec'd by run_pipeline.py),
# where __name__ would just be "__main__" either way and wouldn't
# distinguish which stage is logging.
logger = logging.getLogger("01_fetch_raw_data")


OUTPUT_DIR = Path("data/raw")
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


if __name__ == "__main__":
    run()
