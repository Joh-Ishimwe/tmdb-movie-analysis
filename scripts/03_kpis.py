"""
Step 3: KPI Implementation & Analysis.

Thin wrapper: loads data, calls tmdb_pipeline.kpis, saves results.
The KPI report itself belongs in the notebook/final report, not in the
pipeline's terminal output or logs -- this script only logs progress.
"""

import logging

import pandas as pd

from tmdb_pipeline.cli import PROJECT_ROOT, ensure_dir, force_utf8_stdout, log_loaded, require_file
from tmdb_pipeline.kpis import add_profit_and_roi
from tmdb_pipeline.logging_config import setup_logging

force_utf8_stdout()

logger = logging.getLogger("03_kpis")


CLEAN_FILE = PROJECT_ROOT / "data/processed/tmdb_movies_clean.csv"
PROCESSED_DIR = PROJECT_ROOT / "data/processed"
KPI_FILE = PROCESSED_DIR / "tmdb_movies_with_kpis.csv"


def load_clean_data():
    require_file(CLEAN_FILE)

    df = pd.read_csv(CLEAN_FILE)
    log_loaded(logger, len(df), CLEAN_FILE)
    return df


def run():
    setup_logging()

    try:
        df = load_clean_data()
        df = add_profit_and_roi(df)
        df['is_franchise'] = df['belongs_to_collection'].notna()

        ensure_dir(PROCESSED_DIR)
        df.to_csv(KPI_FILE, index=False)
        logger.info("Saved %d rows to %s", len(df), KPI_FILE)
    except Exception:
        logger.exception("Step 3 (KPIs) failed.")
        raise
