# Copyright 2018-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+
from __future__ import annotations

import os
from argparse import Namespace, ArgumentParser
from shutil import rmtree
from typing import Any

from git import Repo
from .base import BaseRepoCommand


class RemoveArchivedRepo(BaseRepoCommand):
    """remove all locally cloned archived repositories"""

    def get_parser(self, *args: Any, **kwargs: Any) -> ArgumentParser:
        parser = super().get_parser(*args, **kwargs)
        parser.add_argument('-d', '--dry-run', action='store_true', help='dry run only')
        return parser

    def take_action(self, parsed_args: Namespace):
        github = self.login()
        if not github:
            return
        for org_name in self.config.github_orgs:
            for repo in github.organization(org_name).repositories():
                if not repo.archived:
                    continue
                dest_dir = os.path.join(self.config.local_source, repo.name)
                if not os.path.isdir(dest_dir):
                    continue
                local_repo = Repo(dest_dir)
                if local_repo.is_dirty():
                    self.app.LOG.warning('Directory %s is dirty. Skipping.', repo.name)
                    continue
                if parsed_args.dry_run:
                    self.app.LOG.info('Would delete %s', repo.name)
                else:
                    self.app.LOG.info('Deleting archived repo %s', repo.name)
                    rmtree(dest_dir)
