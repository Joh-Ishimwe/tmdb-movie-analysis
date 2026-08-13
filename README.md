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

**Run the full pipeline** (fetch -> clean -> KPIs -> visualize) in one
command -- either directly:
```
python scripts/run_pipeline.py
```
or via the installed console command (from `pip install -e .`'s
`[project.scripts]` entry point):
```
tmdb-pipeline
```

**Or run any stage individually** (each is idempotent and safe to
re-run):
```
python scripts/01_fetch_raw_data.py
python scripts/02_clean_data.py
python scripts/03_kpis.py
python scripts/04_visualizations.py
```

**Or explore interactively**: open `notebook.ipynb` in Jupyter/VS Code --
it walks through the same four steps with explanations for each decision.

All commands assume the project root as the working directory.

## Testing

```
pytest
```

56 tests cover the cleaning transforms, the KPI ranking/aggregation
logic, and the API-facing functions (network calls mocked via
`responses` -- no real API calls, no burned quota). See `tests/`.
