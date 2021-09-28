# Copyright 2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from .chore import Chore

import os
import subprocess


class AuthorsChore(Chore):
    name = 'authors'

    @classmethod
    def is_applicable(cls, repo_path):
        return has_authors_file(repo_path)

    @classmethod
    def is_dirty(cls, repo_path):
        return not has_wazo_author(repo_path)

    @classmethod
    def print_dirty_details(cls, repo_path, repo_name):
        print(authors_path(repo_name))


def authors_path(repo_path):
    return os.path.join(repo_path, 'AUTHORS')


def has_authors_file(repo_path):
    return os.path.isfile(authors_path(repo_path))


def has_wazo_author(repo_path):
    command = [
        'grep',
        '--quiet',
        '--ignore-case',
        'Wazo Communication Inc.',
        authors_path(repo_path),
    ]
    return subprocess.run(command).returncode == 0
