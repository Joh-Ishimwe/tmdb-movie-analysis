"""
Thin CLI wrappers around the tmdb_pipeline package -- one per pipeline
stage (01-04), plus run_pipeline.py to run all four in order. Making
this a real package (rather than a loose folder of scripts) is what lets
the installed `tmdb-pipeline` command (see pyproject.toml's
[project.scripts]) resolve to scripts.run_pipeline:main.
"""
