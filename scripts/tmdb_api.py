"""
Shared TMDb API helpers.

Used by 01_fetch_raw_data.py (movie details) and 02_clean_data.py
(cast & crew credits) so credential loading and the request pattern
aren't duplicated across scripts.
"""

import os

import requests
from dotenv import load_dotenv


def load_credentials():
    """Load TMDB_API_KEY and URL from .env, raising a clear error if missing."""
    load_dotenv()

    api_key = os.getenv("TMDB_API_KEY")
    movie_url = os.getenv("URL")

    if not api_key:
        raise ValueError(
            "TMDB_API_KEY was not found. "
            "Make sure it exists in your .env file."
        )

    if not movie_url:
        raise ValueError(
            "URL was not found. "
            "Make sure it exists in your .env file."
        )

    return api_key, movie_url


def fetch_json(url, api_key, extra_params=None, timeout=15):
    """GET a TMDb endpoint and return the parsed JSON body."""
    params = {"api_key": api_key}
    if extra_params:
        params.update(extra_params)

    response = requests.get(url, params=params, timeout=timeout)

    # Raise an exception for HTTP errors
    response.raise_for_status()

    return response.json()
