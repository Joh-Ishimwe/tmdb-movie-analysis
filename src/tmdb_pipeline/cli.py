"""
Shared helpers for scripts/0N_*.py -- console setup and the "load a
required file or raise with guidance" pattern every stage repeats.
"""

import sys
from pathlib import Path

# Anchor to this installed package's location, not the current working
# directory -- otherwise data/logs/reports land in the wrong place when the
# pipeline is run from inside scripts/ instead of the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def force_utf8_stdout():
    """Force UTF-8 so accented names don't crash print() on Windows (cp1252)."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def require_file(path):
    """Raise a clear, actionable error if path doesn't exist yet. Points
    at the pipeline entry point, not an individual stage -- stages 01-04
    aren't runnable on their own (see scripts/run_pipeline.py)."""
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run the pipeline first: "
            f"python scripts/run_pipeline.py (or the 'tmdb-pipeline' command)."
        )


def log_loaded(logger, count, path):
    """logger is passed in (rather than used from here) so the log line
    is attributed to the calling script/stage, not to this helper."""
    logger.info("Loaded %d movies from %s", count, path)


def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)
