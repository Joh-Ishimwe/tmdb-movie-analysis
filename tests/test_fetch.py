"""Tests for tmdb_pipeline.fetch -- dataset validation and download logic."""

import json

import pytest
import responses

from tmdb_pipeline.fetch import (
    dataset_exists_and_is_valid,
    download_movies,
    load_existing_movies,
    movie_id_exists,
)


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


def test_load_existing_movies_returns_empty_list_when_missing(tmp_path):
    assert load_existing_movies(tmp_path / 'movies.json') == []


def test_load_existing_movies_returns_saved_movies(tmp_path):
    path = tmp_path / 'movies.json'
    path.write_text(json.dumps([{'id': 1}, {'id': 2}]), encoding='utf-8')
    assert load_existing_movies(path) == [{'id': 1}, {'id': 2}]


def test_movie_id_exists_true_when_present():
    existing = [{'id': 1}, {'id': 2}]
    assert movie_id_exists(2, existing) is True


def test_movie_id_exists_false_when_absent():
    existing = [{'id': 1}, {'id': 2}]
    assert movie_id_exists(3, existing) is False


def test_movie_id_exists_false_when_no_existing_movies():
    assert movie_id_exists(1, []) is False


# --- download_movies: skips IDs already present, downloads what's missing ----

URL = 'https://api.example.com/movie/'


@responses.activate
def test_download_movies_skips_ids_already_in_existing_movies():
    responses.add(
        responses.GET, f'{URL}2', json={'id': 2, 'title': 'New'}, status=200
    )
    existing = [{'id': 1, 'title': 'Old'}]

    result = download_movies([1, 2], 'fake-key', URL, existing_movies=existing)

    assert result == [{'id': 2, 'title': 'New'}]
    assert len(responses.calls) == 1  # only the missing ID was fetched


@responses.activate
def test_download_movies_returns_empty_list_when_everything_already_exists():
    existing = [{'id': 1}, {'id': 2}]

    result = download_movies([1, 2], 'fake-key', URL, existing_movies=existing)

    assert result == []
    assert len(responses.calls) == 0  # nothing needed fetching


@responses.activate
def test_download_movies_raises_when_missing_ids_all_fail_and_nothing_exists_yet():
    responses.add(responses.GET, f'{URL}1', json={'status_message': 'nope'}, status=404)

    with pytest.raises(RuntimeError):
        download_movies([1], 'fake-key', URL, existing_movies=[])


@responses.activate
def test_download_movies_does_not_raise_when_a_missing_id_fails_but_dataset_exists():
    # A permanently-failing ID (e.g. the brief's sentinel ID 0) shouldn't
    # break an otherwise-healthy, already-downloaded dataset on every run.
    responses.add(responses.GET, f'{URL}0', json={'status_message': 'nope'}, status=404)
    existing = [{'id': 1}, {'id': 2}]

    result = download_movies([0, 1, 2], 'fake-key', URL, existing_movies=existing)

    assert result == []
