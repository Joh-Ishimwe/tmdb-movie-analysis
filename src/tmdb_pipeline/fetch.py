"""
Step 1: Fetch Movie Data from API.

Pure fetch/validate logic -- no hardcoded file paths, so it's usable from
scripts/01_fetch_raw_data.py, tests, or anywhere else without touching
disk unless explicitly asked to.
"""

import json

import requests

from tmdb_pipeline.api import fetch_json

# Movie IDs required by the project brief.
MOVIE_IDS = [
    0, 299534, 19995, 140607, 299536, 597, 135397,
    420818, 24428, 168259, 99861, 284054, 12445,
    181808, 330457, 351286, 109445, 321612, 260513
]


def dataset_exists_and_is_valid(output_file):
    """
    Return True if output_file exists and contains a non-empty list of
    movie records.
    """
    if not output_file.exists():
        return False

    try:
        with open(output_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            return False

        if len(data) == 0:
            return False

        return True

    except (json.JSONDecodeError, OSError):
        return False


def fetch_movie(movie_id, api_key, movie_url):
    """Fetch one movie's details, with cast/crew bundled into the same
    call via append_to_response=credits -- half the API calls compared
    to a separate /movie/{id}/credits request per movie afterward."""
    return fetch_json(
        f"{movie_url}{movie_id}",
        api_key,
        extra_params={"append_to_response": "credits"},
    )


def download_movies(movie_ids, api_key, movie_url, verbose=True):
    """Fetch every ID in movie_ids, skipping (not raising on) individual
    failures -- a bad ID or one flaky request shouldn't lose the whole
    batch. Raises RuntimeError only if nothing could be downloaded at
    all. Returns the list of successfully fetched movie dicts."""
    if verbose:
        print("Downloading movie data from TMDB...")

    movies = []

    for movie_id in movie_ids:
        if verbose:
            print(f"Fetching movie ID: {movie_id}")

        try:
            movie = fetch_movie(movie_id, api_key, movie_url)

            # Make sure the response actually contains data
            if movie and isinstance(movie, dict):

                # TMDB error responses can contain a "status_code"
                if "status_code" in movie:
                    if verbose:
                        print(
                            f"  Skipping ID {movie_id}: "
                            f"{movie.get('status_message', 'API error')}"
                        )
                    continue

                movies.append(movie)

            elif verbose:
                print(f"  Skipping ID {movie_id}: empty response.")

        except requests.exceptions.Timeout:
            if verbose:
                print(f"  Timeout while fetching ID {movie_id}.")

        except requests.exceptions.ConnectionError:
            if verbose:
                print(f"  Could not connect to TMDB while fetching ID {movie_id}.")

        except requests.exceptions.HTTPError as error:
            if verbose:
                print(f"  HTTP error for ID {movie_id}: {error}")

        except requests.exceptions.RequestException as error:
            if verbose:
                print(f"  Request failed for ID {movie_id}: {error}")

    if not movies:
        raise RuntimeError(
            "No movie data was downloaded. The dataset will NOT be saved."
        )

    if verbose:
        print()
        print(f"Successfully downloaded {len(movies)} movies.")

    return movies
