# TMDb Movie Data Analysis

A movie data analysis pipeline built with Python and Pandas: fetches 19
hand-picked blockbuster movies from the TMDb API, cleans and transforms
the dataset, computes KPIs (best/worst performers, franchise vs.
standalone success, most successful directors), and renders supporting
visualizations.

See [doc/final_report.txt](doc/final_report.txt) for the full writeup of
findings, methodology, and conclusions.

## Project structure

```
notebook.ipynb                  Exploratory workflow -- Steps 1-4 end to end
src/tmdb_pipeline/               The actual reusable logic, as a real installed
                                 package -- import it directly, no path tricks
  api.py                         Credentials + HTTP with retry/backoff
  fetch.py                       Step 1: fetch raw movie data from TMDb
  cleaning.py                    Step 2: clean & preprocess
  kpis.py                        Step 3: KPI analysis
  visualization.py               Step 4: charts (Matplotlib)
  cli.py                         Shared script boilerplate (UTF-8 setup, etc.)
  logging_config.py              Console + logs/pipeline.log setup
scripts/                        Thin CLI wrappers around tmdb_pipeline --
                                 each reads input, calls into the package,
                                 prints/saves output
  01_fetch_raw_data.py
  02_clean_data.py
  03_kpis.py
  04_visualizations.py
  run_pipeline.py               Runs all four stages in order
tests/                          Tests for tmdb_pipeline -- plain imports,
                                 no path tricks needed
data/
  raw/movies.json               Cached raw API response (gitignored)
  processed/                    Cleaned & KPI-enriched CSVs (gitignored)
reports/figures/                Generated chart PNGs (gitignored)
logs/pipeline.log                Timestamped run history (gitignored)
doc/final_report.txt            Key insights, methodology, conclusions
```

Each script stage writes the file the next one reads:
`01 -> data/raw/movies.json -> 02 -> data/processed/tmdb_movies_clean.csv
-> 03 -> data/processed/tmdb_movies_with_kpis.csv -> 04 -> reports/figures/*.png`

The scripts are intentionally thin: `01_fetch_raw_data.py` handles reading
the on-disk cache and writing the result, but the actual fetch/validate
logic is `tmdb_pipeline.fetch`, importable and testable on its own
(`from tmdb_pipeline.cleaning import extract_names`) rather than requiring
file-path-based tricks to load a numbered script.

## Setup

1. **Get a TMDb API key** -- free at
   [themoviedb.org](https://www.themoviedb.org/) under Settings -> API.

2. **Configure credentials**:
   ```
   cp .env.example .env
   ```
   then fill in your `TMDB_API_KEY` in `.env`. `URL` is already set to the
   correct TMDb endpoint.

3. **Install dependencies** (installs runtime + dev + notebook extras --
   pandas, requests, matplotlib, pytest, responses, etc. -- as declared in
   `pyproject.toml`):
   ```
   pip install -e ".[dev,notebook]"
   ```

## Usage

This pipeline has one entry point. Run it end to end (fetch -> clean ->
KPIs -> visualize) either directly:
```
python scripts/run_pipeline.py
```
or via the installed console command (from `pip install -e .`'s
`[project.scripts]` entry point):
```
tmdb-pipeline
```

`scripts/01_fetch_raw_data.py` through `04_visualizations.py` aren't
meant to be run directly -- each is a stage `run_pipeline.py` calls in
order, not a standalone script (running one directly prints an error
telling you to use `run_pipeline.py`/`tmdb-pipeline` instead). Each
stage is still idempotent and safe to rerun as part of the pipeline --
`01` skips re-fetching if a valid cache exists, and `02`-`04` simply
regenerate their output.

**Or explore interactively**: open `notebook.ipynb` in Jupyter/VS Code --
it walks through the same four steps with explanations for each decision.

All commands assume the project root as the working directory.

## Logging

Every stage logs to both the console and `logs/pipeline.log` (timestamp,
level, and which stage/module -- e.g. `tmdb_pipeline.fetch`, `03_kpis`).
If a run fails, the log file has the full traceback and which stage was
running, even after the terminal that ran it is gone. Per-ID fetch
failures log at WARNING (a bad/rate-limited ID doesn't stop the batch);
a stage-ending failure logs at ERROR with the full traceback before
re-raising.

## Testing

```
pytest
```

74 tests cover the cleaning transforms, the KPI ranking/aggregation
logic, and the API-facing functions (network calls mocked via
`responses` -- no real API calls, no burned quota). See `tests/`.
