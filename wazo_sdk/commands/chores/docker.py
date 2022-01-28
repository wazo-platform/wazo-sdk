# Copyright 2021-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import subprocess

from .chore import Chore


class DockerChore(Chore):
    name = 'docker'

    @classmethod
    def print_expectations(cls):
        print('- Dockerfile does not include build-only files in final image')

    @classmethod
    def is_applicable(cls, repo_path):
        return has_dockerfile(repo_path)

    @classmethod
    def is_dirty(cls, repo_path):
        return needs_split_dockerfile(repo_path)

    @classmethod
    def print_dirty_details(cls, repo_path, repo_name):
        print(dockerfile_path(repo_name))


def dockerfile_path(repo_path):
    return os.path.join(repo_path, 'Dockerfile')


def has_dockerfile(repo_path):
    return os.path.isfile(dockerfile_path(repo_path))


def needs_split_dockerfile(repo_path):
    return has_one_dockerfile_from(repo_path) and has_requirements_txt(repo_path)


def has_one_dockerfile_from(repo_path):
    try:
        command = [
            'grep',
            '--ignore-case',
            '--count',
            '^FROM',
            dockerfile_path(repo_path),
        ]
        return subprocess.check_output(command).decode('utf-8').strip() == '1'
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            return False
        raise


def has_requirements_txt(repo_path):
    command = [
        'grep',
        '--quiet',
        '--ignore-case',
        'requirements.txt',
        dockerfile_path(repo_path),
    ]
    return subprocess.run(command).returncode == 0
