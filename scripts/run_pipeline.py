"""
Run the full TMDb movie analysis pipeline end to end:

  1. Fetch raw movie data from the TMDb API      (01_fetch_raw_data.py)
  2. Clean and preprocess it                      (02_clean_data.py)
  3. Compute KPIs                                 (03_kpis.py)
  4. Render visualizations                        (04_visualizations.py)

Each stage writes the file the next one reads, so they run in this fixed
order and stop at the first failure rather than continuing on stale or
missing data.

Usage (from the project root):
    python scripts/run_pipeline.py
"""

import importlib.util
import sys
from pathlib import Path

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
    for label, filename in STAGES:
        print(f"\n{'=' * 60}")
        print(label)
        print("=" * 60)

        module = _load_script(filename)
        module.main()

    print(f"\n{'=' * 60}")
    print("Pipeline complete.")
    print("=" * 60)


def main():
    try:
        run_pipeline()
    except Exception as error:
        print(f"\nPipeline failed: {error}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
