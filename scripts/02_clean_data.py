"""
Step 2: Data Cleaning and Preprocessing.

Thin wrapper: loads the raw dataset, calls tmdb_pipeline.cleaning, saves
the result. No network calls, so no .env credentials needed here.
"""

import json
import logging
from pathlib import Path

import pandas as pd

from tmdb_pipeline.cleaning import clean_data
from tmdb_pipeline.cli import ensure_dir, force_utf8_stdout, log_loaded, require_file
from tmdb_pipeline.logging_config import setup_logging

force_utf8_stdout()

# Named explicitly (not via __name__) so the log always says which
# stage is speaking, whether run standalone or via run_pipeline.py.
logger = logging.getLogger("02_clean_data")


RAW_FILE = Path("data/raw/movies.json")
PROCESSED_DIR = Path("data/processed")
PROCESSED_FILE = PROCESSED_DIR / "tmdb_movies_clean.csv"


def load_raw_data(path):
    require_file(path, "01_fetch_raw_data.py")

    with open(path, "r", encoding="utf-8") as file:
        movies_data = json.load(file)

    log_loaded(logger, len(movies_data), path)
    return pd.DataFrame(movies_data)


def run():
    setup_logging()

    try:
        raw_df = load_raw_data(RAW_FILE)
        df = clean_data(raw_df)

        ensure_dir(PROCESSED_DIR)
        df.to_csv(PROCESSED_FILE, index=False)

        logger.info("Saved %d rows to %s", len(df), PROCESSED_FILE)
    except Exception:
        logger.exception("Step 2 (clean) failed.")
        raise


if __name__ == "__main__":
    run()
