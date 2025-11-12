# Copyright 2018-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import annotations

import logging
from collections.abc import Generator
from functools import cached_property

from cliff.command import Command
from github3 import GitHub, login
from github3.repos import ShortRepository

from wazo_sdk.config import Config


class BaseRepoCommand(Command):
    config: Config
    _github: GitHub | None = None

    def login(self) -> GitHub | None:
        if not self.config.github_orgs:
            self.app.LOG.error('No GitHub organisations configured')
            return None
        if not self.config.github_username:
            self.app.LOG.error('No GitHub username configured')
            return None
        if not self.config.github_token:
            self.app.LOG.error('No GitHub personal access token configured')
            return None

        logging.getLogger('github3').setLevel(logging.WARNING)
        return login(self.config.github_username, self.config.github_token)

    @cached_property
    def github(self) -> GitHub:
        if self._github is None:
            self._github = self.login()
        return self._github

    def iter_all_repositories(self) -> Generator[ShortRepository, None, None]:
        for org_name in self.config.github_orgs:
            yield from self.github.organization(org_name).repositories()
