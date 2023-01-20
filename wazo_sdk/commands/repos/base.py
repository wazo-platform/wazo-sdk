# Copyright 2018-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+
from __future__ import annotations

import logging

from cliff.command import Command
from github3 import login, GitHub

from wazo_sdk.config import Config


class BaseRepoCommand(Command):
    config: Config

    def login(self) -> GitHub | None:
        if not self.config.github_orgs:
            self.app.LOG.error('No GitHub organisations configured')
            return
        if not self.config.github_username:
            self.app.LOG.error('No GitHub username configured')
            return
        if not self.config.github_token:
            self.app.LOG.error('No GitHub personal access token configured')
            return

        logging.getLogger('github3').setLevel(logging.WARNING)
        return login(self.config.github_username, self.config.github_token)
