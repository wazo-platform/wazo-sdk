# Copyright 2022 The Wazo Mypy  (see the MYPY file)
# SPDX-License-Identifier: GPL-3.0-or-later

from .chore import Chore

import configparser
import os


class MypyChore(Chore):
    name = 'mypy'

    @classmethod
    def print_expectations(cls):
        print('- tox linters run mypy')

    @classmethod
    def is_applicable(cls, repo_path):
        return has_tox_linters(repo_path)

    @classmethod
    def is_dirty(cls, repo_path):
        return not has_tox_linters_running_mypy(repo_path)

    @classmethod
    def print_dirty_details(cls, repo_path, repo_name):
        print(tox_file_path(repo_name))


def tox_file_path(repo_path):
    return os.path.join(repo_path, 'tox.ini')


def has_tox_linters(repo_path):
    return os.path.isfile(
        tox_file_path(repo_path)
    ) and 'testenv:linters' in read_tox_config(repo_path)


def read_tox_config(repo_path):
    tox_config = configparser.ConfigParser()
    tox_config.read(tox_file_path(repo_path))
    return tox_config


def has_tox_linters_running_mypy(repo_path):
    tox_config = read_tox_config(repo_path)
    try:
        return 'mypy' in tox_config['testenv:linters']['commands']
    except KeyError:
        return False
