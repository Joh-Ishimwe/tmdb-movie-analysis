"""Tests for tmdb_pipeline.fetch -- dataset validation logic.

No network access here: dataset_exists_and_is_valid() takes the file
path directly, so these just point it at tmp_path fixtures. Network
calls (fetch_movie/download_movies) are exercised via tmdb_pipeline.api,
mocked in test_api.py.
"""

import json

from tmdb_pipeline.fetch import dataset_exists_and_is_valid


def test_missing_file_is_invalid(tmp_path):
    assert dataset_exists_and_is_valid(tmp_path / 'movies.json') is False


def test_empty_list_is_invalid(tmp_path):
    path = tmp_path / 'movies.json'
    path.write_text('[]', encoding='utf-8')
    assert dataset_exists_and_is_valid(path) is False


def test_non_list_json_is_invalid(tmp_path):
    path = tmp_path / 'movies.json'
    path.write_text('{"not": "a list"}', encoding='utf-8')
    assert dataset_exists_and_is_valid(path) is False


def test_corrupt_json_is_invalid(tmp_path):
    path = tmp_path / 'movies.json'
    path.write_text('{not valid json', encoding='utf-8')
    assert dataset_exists_and_is_valid(path) is False


def test_valid_non_empty_list_is_valid(tmp_path):
    path = tmp_path / 'movies.json'
    path.write_text(json.dumps([{'id': 1}]), encoding='utf-8')
    assert dataset_exists_and_is_valid(path) is True
