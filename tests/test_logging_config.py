"""Tests for tmdb_pipeline.logging_config."""

import logging

from tmdb_pipeline.logging_config import setup_logging


def test_setup_logging_creates_log_file(tmp_path, monkeypatch):
    log_dir = tmp_path / 'logs'
    monkeypatch.setattr('tmdb_pipeline.logging_config.LOG_DIR', log_dir)
    monkeypatch.setattr('tmdb_pipeline.logging_config.LOG_FILE', log_dir / 'pipeline.log')

    setup_logging()

    assert log_dir.is_dir()
    assert (log_dir / 'pipeline.log').exists()


def test_setup_logging_writes_formatted_records_to_the_file(tmp_path, monkeypatch):
    log_dir = tmp_path / 'logs'
    log_file = log_dir / 'pipeline.log'
    monkeypatch.setattr('tmdb_pipeline.logging_config.LOG_DIR', log_dir)
    monkeypatch.setattr('tmdb_pipeline.logging_config.LOG_FILE', log_file)

    setup_logging()
    logging.getLogger('some.module').info("something happened")

    contents = log_file.read_text(encoding='utf-8')
    assert "[INFO] some.module: something happened" in contents


def test_setup_logging_quiets_matplotlib():
    setup_logging()
    assert logging.getLogger('matplotlib').level == logging.WARNING
