# Copyright 2018-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import logging
import os

from cliff.command import Command
from git import Repo
from github3 import login


class RepoClone(Command):

    def take_action(self, parsed_args):
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
        github = login(self.config.github_username, self.config.github_token)
        for org_name in self.config.github_orgs:
            for repo in github.organization(org_name).repositories():
                self.app.LOG.info('Cloning %s...', repo.name)
                dest_dir = os.path.join(self.config.local_source, repo.name)
                if os.path.isdir(dest_dir):
                    self.app.LOG.info('Directory %s already exists.', repo.name)
                    continue
                Repo.clone_from(repo.ssh_url, to_path=dest_dir)
