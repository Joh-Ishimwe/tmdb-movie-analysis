"""Tests for tmdb_pipeline.cli -- shared script boilerplate."""

import logging

import pytest

from tmdb_pipeline.cli import ensure_dir, force_utf8_stdout, log_loaded, require_file


def test_require_file_raises_with_prior_step_in_message(tmp_path):
    missing = tmp_path / 'movies.json'
    with pytest.raises(FileNotFoundError, match='01_fetch_raw_data.py'):
        require_file(missing, '01_fetch_raw_data.py')


def test_require_file_does_not_raise_when_present(tmp_path):
    path = tmp_path / 'movies.json'
    path.write_text('[]', encoding='utf-8')
    require_file(path, '01_fetch_raw_data.py')  # no raise


def test_log_loaded_logs_count_and_path_under_caller_logger(caplog):
    logger = logging.getLogger('some.calling.script')
    with caplog.at_level(logging.INFO):
        log_loaded(logger, 18, 'data/raw/movies.json')

    assert len(caplog.records) == 1
    assert caplog.records[0].name == 'some.calling.script'
    assert caplog.records[0].message == "Loaded 18 movies from data/raw/movies.json"


def test_ensure_dir_creates_missing_nested_directory(tmp_path):
    target = tmp_path / 'a' / 'b' / 'c'
    ensure_dir(target)
    assert target.is_dir()


def test_ensure_dir_tolerates_already_existing_directory(tmp_path):
    ensure_dir(tmp_path)  # already exists -- must not raise
    assert tmp_path.is_dir()


def test_force_utf8_stdout_does_not_raise():
    force_utf8_stdout()  # no assertion on stdout itself -- just must not crash
