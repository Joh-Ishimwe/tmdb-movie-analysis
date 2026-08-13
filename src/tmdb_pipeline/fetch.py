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


def fetch_movie(movie_id, api_key, movie_url):
    """One movie's details, with cast/crew bundled in via
    append_to_response=credits -- half the API calls vs. a separate
    /credits request per movie."""
    return fetch_json(
        f"{movie_url}{movie_id}",
        api_key,
        extra_params={"append_to_response": "credits"},
    )


def download_movies(movie_ids, api_key, movie_url):
    """Fetch every ID, skipping individual failures rather than aborting
    the batch. Raises RuntimeError only if nothing downloaded at all."""
    logger.info("Downloading movie data from TMDB...")

    movies = []

    for movie_id in movie_ids:
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
            logger.warning("HTTP error for ID %s: %s", movie_id, error)

        except requests.exceptions.RequestException as error:
            logger.warning("Request failed for ID %s: %s", movie_id, error)

    if not movies:
        raise RuntimeError(
            "No movie data was downloaded. The dataset will NOT be saved."
        )

    logger.info("Successfully downloaded %d movies.", len(movies))

    return movies
