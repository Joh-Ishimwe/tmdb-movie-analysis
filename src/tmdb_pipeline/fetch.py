"""
Step 1: Fetch Movie Data from API.

No hardcoded file paths -- usable from scripts, tests, or anywhere else.
"""

import json
import logging

import requests

from tmdb_pipeline.api import fetch_json

logger = logging.getLogger(__name__)

# Movie IDs required by the project brief.
MOVIE_IDS = [
    0, 299534, 19995, 140607, 299536, 597, 135397,
    420818, 24428, 168259, 99861, 284054, 12445,
    181808, 330457, 351286, 109445, 321612, 260513
]


def dataset_exists_and_is_valid(output_file):
    """True if output_file exists and holds a non-empty list of movies."""
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


def load_existing_movies(output_file):
    """Previously saved movies, or [] if there's nothing valid saved yet."""
    if not dataset_exists_and_is_valid(output_file):
        return []

    with open(output_file, "r", encoding="utf-8") as file:
        return json.load(file)


def movie_id_exists(movie_id, existing_movies):
    """True if movie_id is already present among existing_movies."""
    return any(movie.get('id') == movie_id for movie in existing_movies)


def fetch_movie(movie_id, api_key, movie_url):
    """One movie's details, with cast/crew bundled in via
    append_to_response=credits -- half the API calls vs. a separate
    /credits request per movie."""
    return fetch_json(
        f"{movie_url}{movie_id}",
        api_key,
        extra_params={"append_to_response": "credits"},
    )


def download_movies(movie_ids, api_key, movie_url, existing_movies=None):
    """Fetch every ID not already in existing_movies (e.g. after a
    MOVIE_IDS change), skipping individual failures rather than aborting
    the batch. Raises RuntimeError only if IDs needed fetching, none of
    them succeeded, AND there's no existing dataset to fall back on --
    a permanently-failing ID (e.g. 0) shouldn't break an otherwise-healthy,
    already-downloaded dataset on every run."""
    existing_movies = existing_movies or []
    logger.info("Downloading movie data from TMDB...")

    movies = []
    attempted = 0
    skipped = 0

    for movie_id in movie_ids:
        if movie_id_exists(movie_id, existing_movies):
            skipped += 1
            logger.debug("Movie ID %s already downloaded, skipping.", movie_id)
            continue

        attempted += 1
        logger.info("Fetching movie ID: %s", movie_id)

        try:
            movie = fetch_movie(movie_id, api_key, movie_url)

            # Make sure the response actually contains data
            if movie and isinstance(movie, dict):

                # TMDB error responses can contain a "status_code"
                if "status_code" in movie:
                    logger.warning(
                        "Skipping ID %s: %s",
                        movie_id, movie.get('status_message', 'API error'),
                    )
                    continue

                movies.append(movie)

            else:
                logger.warning("Skipping ID %s: empty response.", movie_id)

        except requests.exceptions.Timeout:
            logger.warning("Timeout while fetching ID %s.", movie_id)

        except requests.exceptions.ConnectionError:
            logger.warning("Could not connect to TMDB while fetching ID %s.", movie_id)

        except requests.exceptions.HTTPError as error:
            # Not str(error) -- it embeds the full request URL, api_key included.
            status = error.response.status_code if error.response is not None else None
            if status == 404:
                logger.warning("Invalid movie ID: %s (not found on TMDB).", movie_id)
            else:
                logger.warning("HTTP error %s for ID %s.", status, movie_id)

        except requests.exceptions.RequestException as error:
            logger.warning("Request failed for ID %s: %s", movie_id, type(error).__name__)

    if skipped:
        logger.info("%d movie(s) already downloaded, skipped.", skipped)

    if attempted and not movies and not existing_movies:
        raise RuntimeError(
            "No movie data was downloaded. The dataset will NOT be saved."
        )

    if movies:
        logger.info("Successfully downloaded %d new movie(s).", len(movies))
    else:
        logger.info("No new movies to download.")

    return movies
