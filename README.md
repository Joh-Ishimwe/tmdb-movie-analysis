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
notebook.ipynb                Exploratory workflow -- Steps 1-4 end to end
scripts/
  01_fetch_raw_data.py        Step 1: fetch raw movie data from TMDb
  02_clean_data.py            Step 2: clean & preprocess
  03_kpis.py                  Step 3: KPI analysis
  04_visualizations.py        Step 4: charts (Matplotlib)
  run_pipeline.py             Runs all four stages in order
  tmdb_api.py                 Shared TMDb API helpers (credentials, requests)
tests/                        Automated tests for the pipeline logic
data/
  raw/movies.json             Cached raw API response (gitignored)
  processed/                  Cleaned & KPI-enriched CSVs (gitignored)
reports/figures/              Generated chart PNGs (gitignored)
doc/final_report.txt          Key insights, methodology, conclusions
```

Each script stage writes the file the next one reads:
`01 -> data/raw/movies.json -> 02 -> data/processed/tmdb_movies_clean.csv
-> 03 -> data/processed/tmdb_movies_with_kpis.csv -> 04 -> reports/figures/*.png`

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
command:
```
python scripts/run_pipeline.py
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

43 tests cover the cleaning transforms, the KPI ranking/aggregation
logic, and the API-facing functions (network calls mocked via
`responses` -- no real API calls, no burned quota). See `tests/`.
