"""tmdb_pipeline -- reusable logic for the TMDb movie analysis pipeline.

Split by pipeline stage, matching the project brief's Steps 1-4:
  api.py            Credentials + HTTP (retry/backoff) shared by fetch.py
  fetch.py          Step 1: fetch raw movie data from TMDb
  cleaning.py       Step 2: clean & preprocess
  kpis.py           Step 3: KPI analysis
  visualization.py  Step 4: charts (Matplotlib)

Each scripts/0N_*.py file is a thin CLI wrapper around these: read input,
call the relevant function(s) here, print/save output. That split is what
makes this importable and testable directly (`from tmdb_pipeline.cleaning
import extract_names`) instead of needing file-path-based importlib
tricks to load a numbered script.
"""

__version__ = "1.0.0"
