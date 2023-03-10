# Copyright 2021-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from .chore import Chore

import os
import subprocess


class AuthorsChore(Chore):
    name = 'authors'

    @classmethod
    def print_expectations(cls) -> None:
        print('- AUTHORS file includes Wazo Communication Inc.')

    @classmethod
    def is_applicable(cls, repo_path: str) -> bool:
        return has_authors_file(repo_path)

    @classmethod
    def is_dirty(cls, repo_path: str) -> bool:
        return not has_wazo_author(repo_path)

    @classmethod
    def print_dirty_details(cls, repo_path: str, repo_name: str) -> None:
        print(authors_path(repo_name))


def authors_path(repo_path: str) -> str:
    return os.path.join(repo_path, 'AUTHORS')


def has_authors_file(repo_path: str) -> bool:
    return os.path.isfile(authors_path(repo_path))


def has_wazo_author(repo_path: str) -> bool:
    command = [
        'grep',
        '--quiet',
        '--ignore-case',
        'Wazo Communication Inc.',
        authors_path(repo_path),
    ]
    return subprocess.run(command).returncode == 0
