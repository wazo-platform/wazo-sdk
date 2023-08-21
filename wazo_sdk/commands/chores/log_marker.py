# Copyright 2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
import subprocess

from .chore import Chore


class LogMarkerChore(Chore):
    name = 'log-marker'

    @classmethod
    def print_expectations(cls) -> None:
        print('- integration tests mark logs with test beginning and end')

    @classmethod
    def is_applicable(cls, repo_path: str) -> bool:
        return has_integration_tests(repo_path)

    @classmethod
    def is_dirty(cls, repo_path: str) -> bool:
        return not uses_log_marker(repo_path)

    @classmethod
    def print_dirty_details(cls, repo_path: str, repo_name: str) -> None:
        print(integration_tests_path(repo_name))


def integration_tests_path(repo_path: str) -> str:
    return os.path.join(repo_path, 'integration_tests')


def has_integration_tests(repo_path: str) -> bool:
    return os.path.isdir(integration_tests_path(repo_path))


def uses_log_marker(repo_path: str) -> bool:
    try:
        command = [
            'grep',
            '--recursive',
            '--count',
            'mark_logs_test_start',
            integration_tests_path(repo_path),
        ]
        has_start = subprocess.check_output(command).decode('utf-8').strip() != '0'
        command = [
            'grep',
            '--recursive',
            '--count',
            'mark_logs_test_end',
            integration_tests_path(repo_path),
        ]
        has_end = subprocess.check_output(command).decode('utf-8').strip() != '0'
        return has_start and has_end
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            return False
        raise
