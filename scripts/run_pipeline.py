"""
Run the full pipeline end to end: fetch -> clean -> KPIs -> visualize.

Each stage writes the file the next one reads, so they run in this fixed
order and stop at the first failure.

Usage (from the project root): python scripts/run_pipeline.py
"""

import importlib.util
import logging
import sys
from pathlib import Path

from tmdb_pipeline.logging_config import setup_logging

logger = logging.getLogger("run_pipeline")

SCRIPTS_DIR = Path(__file__).resolve().parent

STAGES = [
    ("Step 1: Fetch Raw Data", "01_fetch_raw_data.py"),
    ("Step 2: Clean & Preprocess", "02_clean_data.py"),
    ("Step 3: KPI Analysis", "03_kpis.py"),
    ("Step 4: Visualizations", "04_visualizations.py"),
]


def _load_script(filename):
    """Numbered filenames (01_..., 02_...) aren't valid Python module
    names, so each stage is loaded by file path instead of a normal
    `import`."""
    alias = filename[:-3]  # strip ".py"
    path = SCRIPTS_DIR / filename
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


def run_pipeline():
    current_stage = None
    try:
        for label, filename in STAGES:
            current_stage = label
            logger.info("=" * 60)
            logger.info(label)
            logger.info("=" * 60)

            module = _load_script(filename)
            module.run()

        logger.info("=" * 60)
        logger.info("Pipeline complete.")
        logger.info("=" * 60)
    except Exception:
        # Each stage's own run() already logged the full traceback under
        # its own name; this adds the one thing it couldn't know itself --
        # which stage was running when the pipeline stopped.
        logger.error("Pipeline stopped during: %s", current_stage)
        raise


def main():
    setup_logging()
    run_pipeline()


if __name__ == "__main__":
    main()
