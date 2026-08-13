"""
Shared helpers for scripts/0N_*.py -- console setup and the "load a
required file or raise with guidance" pattern every stage repeats.
"""

import sys


def force_utf8_stdout():
    """Force UTF-8 so accented names don't crash print() on Windows (cp1252)."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def require_file(path, prior_step):
    """Raise a clear, actionable error if path doesn't exist yet."""
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run {prior_step} first.")


def log_loaded(logger, count, path):
    """logger is passed in (rather than used from here) so the log line
    is attributed to the calling script/stage, not to this helper."""
    logger.info("Loaded %d movies from %s", count, path)


def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)
