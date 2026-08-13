"""Tests for tmdb_pipeline.api -- credentials and HTTP with retry/backoff.

This is the one place in the pipeline that touches the network, so it's
the one file that needs mocking: `responses` intercepts HTTP so nothing
here ever hits the real TMDb API or burns API quota.
"""

import pytest
import requests
import responses

from tmdb_pipeline import api


# --- load_credentials ----------------------------------------------------------

def test_load_credentials_returns_key_and_url_when_present(monkeypatch):
    monkeypatch.setattr(api, 'load_dotenv', lambda *a, **kw: None)
    monkeypatch.setenv('TMDB_API_KEY', 'fake-key')
    monkeypatch.setenv('URL', 'https://api.example.com/movie/')

    api_key, movie_url = api.load_credentials()

    assert api_key == 'fake-key'
    assert movie_url == 'https://api.example.com/movie/'


def test_load_credentials_raises_when_api_key_missing(monkeypatch):
    monkeypatch.setattr(api, 'load_dotenv', lambda *a, **kw: None)
    monkeypatch.delenv('TMDB_API_KEY', raising=False)
    monkeypatch.setenv('URL', 'https://api.example.com/movie/')

    with pytest.raises(ValueError, match='TMDB_API_KEY'):
        api.load_credentials()


def test_load_credentials_raises_when_url_missing(monkeypatch):
    monkeypatch.setattr(api, 'load_dotenv', lambda *a, **kw: None)
    monkeypatch.setenv('TMDB_API_KEY', 'fake-key')
    monkeypatch.delenv('URL', raising=False)

    with pytest.raises(ValueError, match='URL'):
        api.load_credentials()


# --- fetch_json --------------------------------------------------------------

@responses.activate
def test_fetch_json_returns_parsed_body_on_success():
    responses.add(
        responses.GET,
        'https://api.example.com/movie/597',
        json={'id': 597, 'title': 'Titanic'},
        status=200,
    )

    result = api.fetch_json('https://api.example.com/movie/597', 'fake-key')

    assert result == {'id': 597, 'title': 'Titanic'}


@responses.activate
def test_fetch_json_raises_on_http_error():
    responses.add(
        responses.GET,
        'https://api.example.com/movie/0',
        json={'status_message': 'not found'},
        status=404,
    )

    with pytest.raises(requests.exceptions.HTTPError):
        api.fetch_json('https://api.example.com/movie/0', 'fake-key')

    # 404 ("not found") isn't in the retry list -- retrying it would just
    # waste calls, so exactly one request should have been made.
    assert len(responses.calls) == 1


@responses.activate
def test_fetch_json_merges_extra_params_into_query():
    responses.add(
        responses.GET,
        'https://api.example.com/movie/597/credits',
        json={'cast': []},
        status=200,
    )

    api.fetch_json(
        'https://api.example.com/movie/597/credits',
        'fake-key',
        extra_params={'language': 'en-US'},
    )

    request = responses.calls[0].request
    assert 'api_key=fake-key' in request.url
    assert 'language=en-US' in request.url


# --- retry/backoff on transient failures ---------------------------------

def _fast_retry_session():
    """A session with the same retry policy as production but negligible
    backoff, so these tests exercise the real Retry/HTTPAdapter machinery
    without actually waiting seconds between attempts."""
    return api._build_session(total=3, backoff_factor=0.01)


@responses.activate
def test_fetch_json_retries_transient_server_errors_then_succeeds(monkeypatch):
    monkeypatch.setattr(api, '_session', _fast_retry_session())

    url = 'https://api.example.com/movie/597'
    responses.add(responses.GET, url, status=503)   # transient failure #1
    responses.add(responses.GET, url, status=503)   # transient failure #2
    responses.add(responses.GET, url, json={'id': 597}, status=200)  # succeeds

    result = api.fetch_json(url, 'fake-key')

    assert result == {'id': 597}
    assert len(responses.calls) == 3


@responses.activate
def test_fetch_json_raises_after_exhausting_retries(monkeypatch):
    monkeypatch.setattr(api, '_session', _fast_retry_session())

    url = 'https://api.example.com/movie/597'
    # total=3 -> 1 initial attempt + 3 retries = 4 attempts, all failing.
    for _ in range(4):
        responses.add(responses.GET, url, status=503)

    with pytest.raises(requests.exceptions.HTTPError):
        api.fetch_json(url, 'fake-key')

    assert len(responses.calls) == 4
