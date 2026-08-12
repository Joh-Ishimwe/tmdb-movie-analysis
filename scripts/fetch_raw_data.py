import json
from pathlib import Path

import requests
from dotenv import load_dotenv
import os


# 1. Load environment variables

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")

if not API_KEY:
    raise ValueError(
        "TMDB_API_KEY was not found. "
        "Make sure it exists in your .env file."
    )


# 2. Movie IDs required by the project

MOVIE_IDS = [
    0, 299534, 19995, 140607, 299536, 597, 135397,
    420818, 24428, 168259, 99861, 284054, 12445,
    181808, 330457, 351286, 109445, 321612, 260513
]


# 3. File where the raw dataset will be stored

OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "movies.json"



# 4. Check whether a valid dataset already exists

def dataset_exists_and_is_valid():
    """
    Return True if movies.json exists and contains
    a non-empty list of movie records.
    """

    if not OUTPUT_FILE.exists():
        return False

    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            return False

        if len(data) == 0:
            return False

        return True

    except (json.JSONDecodeError, OSError):
        return False


# 5. Fetch one movie from TMDB

def fetch_movie(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"

    params = {
        "api_key": API_KEY
    }

    response = requests.get(
        url,
        params=params,
        timeout=15
    )

    # Raise an exception for HTTP errors
    response.raise_for_status()

    return response.json()



# 6. Fetch all required movies

def download_movies():

    print("Downloading movie data from TMDB...")

    movies = []

    for movie_id in MOVIE_IDS:

        print(f"Fetching movie ID: {movie_id}")

        try:
            movie = fetch_movie(movie_id)

            # Make sure the response actually contains data
            if movie and isinstance(movie, dict):

                # TMDB error responses can contain an "status_code"
                if "status_code" in movie:
                    print(
                        f"  Skipping ID {movie_id}: "
                        f"{movie.get('status_message', 'API error')}"
                    )
                    continue

                movies.append(movie)

            else:
                print(f"  Skipping ID {movie_id}: empty response.")

        except requests.exceptions.Timeout:
            print(f"  Timeout while fetching ID {movie_id}.")

        except requests.exceptions.ConnectionError:
            print(
                f"  Could not connect to TMDB while fetching "
                f"ID {movie_id}."
            )

        except requests.exceptions.HTTPError as error:
            print(
                f"  HTTP error for ID {movie_id}: "
                f"{error}"
            )

        except requests.exceptions.RequestException as error:
            print(
                f"  Request failed for ID {movie_id}: "
                f"{error}"
            )

    # Make sure we didn't download an empty dataset

    if not movies:
        raise RuntimeError(
            "No movie data was downloaded. "
            "The dataset will NOT be saved."
        )

    
    # Create the directory if it doesn't exist

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Save the raw dataset

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            movies,
            file,
            indent=2,
            ensure_ascii=False
        )

    print()
    print(f"Successfully downloaded {len(movies)} movies.")
    print(f"Dataset saved to: {OUTPUT_FILE}")


# 7. Main program


def main():

    # If a valid dataset already exists,
    # don't call the API again.
    if dataset_exists_and_is_valid():

        print(
            f"Dataset already exists at: {OUTPUT_FILE}"
        )
        print("Skipping API download.")

        return

    # Otherwise download it
    download_movies()


if __name__ == "__main__":
    main()