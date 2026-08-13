"""Tests for scripts/01_fetch_raw_data.py and scripts/tmdb_api.py.

This is the one file in the pipeline that touches the network, so it's the
one place these tests need mocking: `responses` intercepts HTTP so nothing
here ever hits the real TMDb API or burns API quota.
"""

import json

import pytest
import requests
import responses


# --- dataset_exists_and_is_valid (01_fetch_raw_data.py) ----------------------

def test_missing_file_is_invalid(fetch_raw_data, tmp_path, monkeypatch):
    monkeypatch.setattr(fetch_raw_data, 'OUTPUT_FILE', tmp_path / 'movies.json')
    assert fetch_raw_data.dataset_exists_and_is_valid() is False


def test_empty_list_is_invalid(fetch_raw_data, tmp_path, monkeypatch):
    path = tmp_path / 'movies.json'
    path.write_text('[]', encoding='utf-8')
    monkeypatch.setattr(fetch_raw_data, 'OUTPUT_FILE', path)
    assert fetch_raw_data.dataset_exists_and_is_valid() is False


def test_non_list_json_is_invalid(fetch_raw_data, tmp_path, monkeypatch):
    path = tmp_path / 'movies.json'
    path.write_text('{"not": "a list"}', encoding='utf-8')
    monkeypatch.setattr(fetch_raw_data, 'OUTPUT_FILE', path)
    assert fetch_raw_data.dataset_exists_and_is_valid() is False


def test_corrupt_json_is_invalid(fetch_raw_data, tmp_path, monkeypatch):
    path = tmp_path / 'movies.json'
    path.write_text('{not valid json', encoding='utf-8')
    monkeypatch.setattr(fetch_raw_data, 'OUTPUT_FILE', path)
    assert fetch_raw_data.dataset_exists_and_is_valid() is False


def test_valid_non_empty_list_is_valid(fetch_raw_data, tmp_path, monkeypatch):
    path = tmp_path / 'movies.json'
    path.write_text(json.dumps([{'id': 1}]), encoding='utf-8')
    monkeypatch.setattr(fetch_raw_data, 'OUTPUT_FILE', path)
    assert fetch_raw_data.dataset_exists_and_is_valid() is True


# --- load_credentials (tmdb_api.py) -------------------------------------------

def test_load_credentials_returns_key_and_url_when_present(tmdb_api, monkeypatch):
    monkeypatch.setattr(tmdb_api, 'load_dotenv', lambda *a, **kw: None)
    monkeypatch.setenv('TMDB_API_KEY', 'fake-key')
    monkeypatch.setenv('URL', 'https://api.example.com/movie/')

    api_key, movie_url = tmdb_api.load_credentials()

    assert api_key == 'fake-key'
    assert movie_url == 'https://api.example.com/movie/'


def test_load_credentials_raises_when_api_key_missing(tmdb_api, monkeypatch):
    monkeypatch.setattr(tmdb_api, 'load_dotenv', lambda *a, **kw: None)
    monkeypatch.delenv('TMDB_API_KEY', raising=False)
    monkeypatch.setenv('URL', 'https://api.example.com/movie/')

    with pytest.raises(ValueError, match='TMDB_API_KEY'):
        tmdb_api.load_credentials()


def test_load_credentials_raises_when_url_missing(tmdb_api, monkeypatch):
    monkeypatch.setattr(tmdb_api, 'load_dotenv', lambda *a, **kw: None)
    monkeypatch.setenv('TMDB_API_KEY', 'fake-key')
    monkeypatch.delenv('URL', raising=False)

    with pytest.raises(ValueError, match='URL'):
        tmdb_api.load_credentials()


# --- fetch_json (tmdb_api.py) --------------------------------------------------

@responses.activate
def test_fetch_json_returns_parsed_body_on_success(tmdb_api):
    responses.add(
        responses.GET,
        'https://api.example.com/movie/597',
        json={'id': 597, 'title': 'Titanic'},
        status=200,
    )

    result = tmdb_api.fetch_json('https://api.example.com/movie/597', 'fake-key')

    assert result == {'id': 597, 'title': 'Titanic'}


@responses.activate
def test_fetch_json_raises_on_http_error(tmdb_api):
    responses.add(
        responses.GET,
        'https://api.example.com/movie/0',
        json={'status_message': 'not found'},
        status=404,
    )

    with pytest.raises(requests.exceptions.HTTPError):
        tmdb_api.fetch_json('https://api.example.com/movie/0', 'fake-key')


@responses.activate
def test_fetch_json_merges_extra_params_into_query(tmdb_api):
    responses.add(
        responses.GET,
        'https://api.example.com/movie/597/credits',
        json={'cast': []},
        status=200,
    )

    tmdb_api.fetch_json(
        'https://api.example.com/movie/597/credits',
        'fake-key',
        extra_params={'language': 'en-US'},
    )

    request = responses.calls[0].request
    assert 'api_key=fake-key' in request.url
    assert 'language=en-US' in request.url
