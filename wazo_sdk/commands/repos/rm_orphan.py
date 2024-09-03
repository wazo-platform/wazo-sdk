# Copyright 2018-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import annotations

import os
from argparse import ArgumentParser, Namespace
from shutil import rmtree
from typing import Any

from git import InvalidGitRepositoryError, Repo

from .base import BaseRepoCommand


class RemoveOrphanRepo(BaseRepoCommand):
    """remove orphan locally repositories"""

    def get_parser(self, *args: Any, **kwargs: Any) -> ArgumentParser:
        parser = super().get_parser(*args, **kwargs)
        parser.add_argument('-d', '--dry-run', action='store_true', help='dry run only')
        parser.add_argument(
            '-e', '--exclude', default=[], nargs="*", help='repo names to exclude'
        )
        return parser

    def take_action(self, parsed_args: Namespace) -> None:
        remote_repos = set()
        archived_repos = set()
        self.app.LOG.info('Fetching repositories...')
        for repo in self.iter_all_repositories():
            if repo.archived:
                archived_repos.add(repo.name)
            else:
                remote_repos.add(repo.name)

        for directory in os.listdir(self.config.local_source):
            if directory in remote_repos:
                continue

            local_path = os.path.join(self.config.local_source, directory)
            try:
                local_repo = Repo(local_path)
            except InvalidGitRepositoryError:
                continue

            reason = 'Orphan'
            if directory in archived_repos:
                reason = 'Archived'

            if local_repo.is_dirty():
                self.app.LOG.warning('Directory %s is dirty. Skipping', directory)
                continue

            if parsed_args.dry_run:
                self.app.LOG.info('Would delete %s (%s)', directory, reason)
                continue

            self.app.LOG.info('Deleting orphan repo %s (%s)...', directory, reason)
            if not self.confirm_delete(local_path):
                self.app.LOG.info('Aborted')
                continue

            rmtree(local_path)
            self.app.LOG.info('Deleted')

    def confirm_delete(self, path: str) -> bool:
        while True:
            message = f'Are you sure to delete {path} [y/n]? '
            answer = input(message).lower()
            if answer not in ('y', 'n'):
                print('Invalid answer.')
                continue
            else:
                break

        if answer == 'n':
            return False
        return True
