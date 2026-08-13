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
    """A requests Session with automatic retry + exponential backoff on
    transient failures -- connection errors, TMDb rate-limiting (429), and
    server-side errors (5xx). A single flaky response no longer fails the
    whole fetch run. 4xx errors other than 429 (e.g. 404 for a bad movie
    ID) are NOT retried -- retrying "not found" just wastes calls.

    total/backoff_factor are parameters (rather than hardcoded) so tests
    can build a session with negligible backoff and still exercise the
    real Retry/HTTPAdapter machinery, instead of actually waiting seconds
    between retry attempts."""
    retry = Retry(
        total=total,
        backoff_factor=backoff_factor,  # default sleeps ~1s, 2s, 4s
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,  # let response.raise_for_status() below
                                 # be the single place that turns a final
                                 # failure into an exception
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
