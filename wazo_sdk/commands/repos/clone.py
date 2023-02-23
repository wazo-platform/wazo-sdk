# Copyright 2018-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+
from __future__ import annotations

from argparse import Namespace, ArgumentParser
import os
from typing import Any

from git import Repo

from .base import BaseRepoCommand


class RepoClone(BaseRepoCommand):
    """clone all repos from all organisations"""

    def get_parser(self, *args: Any, **kwargs: Any) -> ArgumentParser:
        parser = super().get_parser(*args, **kwargs)
        parser.add_argument(
            '-a',
            '--include-archived',
            action='store_true',
            help='include archived repos',
        )
        return parser

    def take_action(self, parsed_args: Namespace) -> None:
        for repo in self.iter_all_repositories():
            if repo.archived and not parsed_args.include_archived:
                self.app.LOG.info('Skipping archived repo %s...', repo.name)
                continue
            self.app.LOG.info('Cloning %s...', repo.name)
            dest_dir = os.path.join(self.config.local_source, repo.name)
            if os.path.isdir(dest_dir):
                self.app.LOG.info('Directory %s already exists.', repo.name)
                continue
            Repo.clone_from(repo.ssh_url, to_path=dest_dir)
