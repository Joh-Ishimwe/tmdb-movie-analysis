"""
Shared pytest fixtures.

The pipeline scripts are named 01_..., 02_..., etc. -- not valid Python
module names -- so they can't be `import`ed normally. This loads each one
by file path instead, under a clean alias, once per test session.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"


def _load_script(filename, alias):
    path = SCRIPTS_DIR / filename
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session", autouse=True)
def _scripts_on_sys_path():
    """The numbered scripts do `from tmdb_api import ...`, which resolves
    because Python auto-adds a script's own directory to sys.path when it's
    run directly. Recreate that here so the same import works under pytest."""
    sys.path.insert(0, str(SCRIPTS_DIR))
    yield
    sys.path.remove(str(SCRIPTS_DIR))


@pytest.fixture(scope="session")
def clean_data(_scripts_on_sys_path):
    """scripts/02_clean_data.py -- loading it calls load_credentials(), so
    a real .env with TMDB_API_KEY/URL must exist (same as running it directly)."""
    return _load_script("02_clean_data.py", "clean_data")


@pytest.fixture(scope="session")
def kpis(_scripts_on_sys_path):
    """scripts/03_kpis.py -- pure pandas, no credentials needed to import."""
    return _load_script("03_kpis.py", "kpis")


@pytest.fixture(scope="session")
def fetch_raw_data(_scripts_on_sys_path):
    """scripts/01_fetch_raw_data.py -- also calls load_credentials() at import."""
    return _load_script("01_fetch_raw_data.py", "fetch_raw_data")


@pytest.fixture(scope="session")
def tmdb_api(_scripts_on_sys_path):
    """scripts/tmdb_api.py loaded directly, for testing it in isolation
    (separately from whatever clean_data/fetch_raw_data imported)."""
    return _load_script("tmdb_api.py", "tmdb_api")
