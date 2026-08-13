"""
Shared TMDb API helpers: credential loading and an HTTP GET with
automatic retry/backoff. Used by fetch.py (Step 1).
"""

import os

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def _build_session(total=3, backoff_factor=1):
    """Session with retry + exponential backoff on connection errors,
    429, and 5xx. Other 4xx (e.g. 404) aren't retried -- pointless.

    total/backoff_factor are parameters so tests can use a fast session
    without actually waiting between retries."""
    retry = Retry(
        total=total,
        backoff_factor=backoff_factor,  # default sleeps ~1s, 2s, 4s
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,  # fetch_json's raise_for_status() handles it
    )

    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


_session = _build_session()


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
    """GET a TMDb endpoint and return the parsed JSON body. Transient
    failures (connection errors, 429, 5xx) are retried with exponential
    backoff before this raises."""
    params = {"api_key": api_key}
    if extra_params:
        params.update(extra_params)

    response = _session.get(url, params=params, timeout=timeout)

    # Raise an exception for HTTP errors
    response.raise_for_status()

    return response.json()
