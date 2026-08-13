"""
Central logging setup: console output (for watching a run live) plus a
persistent logs/pipeline.log file, so a failure after the terminal is
gone can still be traced by what happened, where (module), and when
(timestamp).
"""

import logging

from tmdb_pipeline.cli import PROJECT_ROOT

LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "pipeline.log"


def setup_logging(level=logging.INFO):
    """Configure console + file logging. Safe to call more than once
    (force=True resets handlers) -- each script's main() calls this, and
    run_pipeline.py runs all four in one process."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
        force=True,
    )

    # Third-party libraries inherit the root level above and would
    # otherwise flood the pipeline's own log with their internal INFO
    # chatter (matplotlib logs one of these per chart rendered).
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
