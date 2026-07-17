# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import annotations

from wazo_sdk.config import DEFAULT_EXCLUDES, Config


def _config_with_file_config(file_config: dict) -> Config:
    config = Config.__new__(Config)
    config._file_config = file_config  # type: ignore[assignment]
    return config


class TestExclude:
    def test_defaults_when_not_configured(self) -> None:
        config = _config_with_file_config({})

        assert config.exclude == DEFAULT_EXCLUDES

    def test_merges_user_excludes_after_defaults(self) -> None:
        config = _config_with_file_config({'exclude': ['*.pyc', 'venv']})

        assert config.exclude == [*DEFAULT_EXCLUDES, '*.pyc', 'venv']

    def test_dedups_when_user_repeats_a_default(self) -> None:
        config = _config_with_file_config({'exclude': ['.git', 'venv']})

        assert config.exclude == [*DEFAULT_EXCLUDES, 'venv']
