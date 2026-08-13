"""tmdb_pipeline -- reusable logic for the TMDb movie analysis pipeline.

One module per step: api.py (shared HTTP/credentials), fetch.py (Step 1),
cleaning.py (Step 2), kpis.py (Step 3), visualization.py (Step 4).
scripts/0N_*.py are thin CLI wrappers around these.
"""

__version__ = "1.0.0"
