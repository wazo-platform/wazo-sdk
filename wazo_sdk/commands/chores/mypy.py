# Copyright 2022-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
from configparser import ConfigParser

from .chore import Chore


class MypyChore(Chore):
    name = 'mypy'

    @classmethod
    def print_expectations(cls) -> None:
        print('- tox linters run mypy')

    @classmethod
    def is_applicable(cls, repo_path: str) -> bool:
        return has_tox_linters(repo_path)

    @classmethod
    def is_dirty(cls, repo_path: str) -> bool:
        return not has_tox_linters_running_mypy(repo_path)

    @classmethod
    def print_dirty_details(cls, repo_path: str, repo_name: str) -> None:
        print(tox_file_path(repo_name))


def tox_file_path(repo_path: str) -> str:
    return os.path.join(repo_path, 'tox.ini')


def has_tox_linters(repo_path: str) -> bool:
    return os.path.isfile(
        tox_file_path(repo_path)
    ) and 'testenv:linters' in read_tox_config(repo_path)


def read_tox_config(repo_path: str) -> ConfigParser:
    tox_config = ConfigParser()
    tox_config.read(tox_file_path(repo_path))
    return tox_config


def has_tox_linters_running_mypy(repo_path: str) -> bool:
    tox_config = read_tox_config(repo_path)
    try:
        return 'mypy' in tox_config['testenv:linters']['commands']
    except KeyError:
        return False
