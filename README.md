# TMDB Movie Data Analysis

A Pandas + TMDb API pipeline that fetches a set of blockbuster movies, cleans and
reshapes the raw JSON into a tidy dataset, and analyzes it for financial and
popularity KPIs, franchise/director performance, and box-office trends.

## Repository structure

```
.
├── data/
│   └── processed/
│       └── tmdb_movies_clean.csv   # cleaned dataset written by the notebook (Step 2)
├── notebooks/
│   └── tmdb_movie_analysis.ipynb   # the full pipeline: fetch → clean → KPIs → charts
├── reports/
│   └── figures/         # PNG charts saved by the notebook (Step 4)
├── requirements.txt
└── .env                 # holds TMDB_API_KEY — not committed
```

## Setup

1. **Get a TMDb API key**: create a free account at [themoviedb.org](https://www.themoviedb.org/),
   then generate a key under Settings → API.
2. **Create `.env`** in the project root:
   ```
   TMDB_API_KEY=your_key_here
   ```
3. **Create a virtual environment and install dependencies**:
   ```
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   pip install -r requirements.txt
   ```
4. **Run the notebook**: open `notebooks/tmdb_movie_analysis.ipynb` in Jupyter/VS Code
   and run all cells top to bottom. It fetches from the live TMDb API, so it needs
   network access and a valid key; it writes the cleaned CSV to `data/processed/`
   and the charts to `reports/figures/`.

## What the notebook does

- **Step 1 — Fetch**: pulls 19 movie IDs from `/movie/{id}` (one ID, `0`, doesn't
  exist and is skipped, leaving 18 movies) and their cast/crew from
  `/movie/{id}/credits`.
- **Step 2 — Clean**: flattens nested JSON fields (genres, collection, production
  companies/countries, spoken languages) into `|`-separated strings, fixes dtypes,
  treats zero budget/revenue/runtime and zero-vote ratings as missing, converts
  budget/revenue to million-USD, and reorders/finalizes the columns.
- **Step 3 — KPIs**: ranks movies by revenue, budget, profit, ROI, votes, rating,
  and popularity via a reusable ranking function; runs two example filtered
  searches; compares franchise vs. standalone performance; and ranks franchises
  and directors.
- **Step 4 — Visualization**: revenue vs. budget, ROI by genre, popularity vs.
  rating, yearly revenue trend, and a franchise-vs-standalone comparison — all
  saved as PNGs.

**Dataset caveat**: the 18 movies are a specific hand-picked list of blockbuster
franchise entries (Avengers, Star Wars, Avatar, Jurassic World, etc.), not a
representative sample of all movies. Some queries in Step 3 (e.g. searching for
a Bruce Willis sci-fi film, or a Tarantino/Uma Thurman film) correctly return zero
results because no such movie was fetched — this is a property of the fixed ID
list in the project brief, not a bug in the filtering logic. Findings are scoped
to this dataset; see the notebook's closing "Key Insights & Conclusions" section
for details.

## Key findings (summary)

- *Avatar* and *Avengers: Endgame* lead on revenue and profit; *Avatar*, *Titanic*,
  and *Jurassic World* have the best ROI, while *Star Wars: The Last Jedi* has the
  weakest.
- The Avengers Collection is the top-performing franchise ($7.78B total revenue
  across 4 films); James Cameron is the top-performing director ($5.19B combined
  from *Avatar* and *Titanic*).
- Within this sample, the two standalone films (*Titanic*, *Beauty and the Beast*)
  actually edge out franchise entries on mean revenue and ROI — franchise status
  correlates with release volume more than with better per-movie economics.

Full methodology and figures are in `notebooks/tmdb_movie_analysis.ipynb`.
