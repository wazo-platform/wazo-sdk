# Copyright 2018-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import os

from cliff.command import Command

from .chores.chore import Chore

# Those classes need to be imported to be listed
from .chores.docker import DockerChore  # noqa
from .chores.authors import AuthorsChore  # noqa


ARCHIVES = set(
    (
        'sphinx-git',
        'wazo-admin-ui',
        'wazo-admin-ui-call-filter',
        'wazo-admin-ui-call-permission',
        'wazo-admin-ui-cdr',
        'wazo-admin-ui-conference',
        'wazo-admin-ui-context',
        'wazo-admin-ui-device',
        'wazo-admin-ui-entity',
        'wazo-admin-ui-extension',
        'wazo-admin-ui-funckey',
        'wazo-admin-ui-general-settings',
        'wazo-admin-ui-group',
        'wazo-admin-ui-incall',
        'wazo-admin-ui-ivr',
        'wazo-admin-ui-line',
        'wazo-admin-ui-market',
        'wazo-admin-ui-moh',
        'wazo-admin-ui-outcall',
        'wazo-admin-ui-paging',
        'wazo-admin-ui-parking-lot',
        'wazo-admin-ui-schedule',
        'wazo-admin-ui-sound',
        'wazo-admin-ui-switchboard',
        'wazo-admin-ui-trunk',
        'wazo-admin-ui-user',
        'wazo-admin-ui-voicemail',
        'wazo-admin-ui-webhook',
        'wazo-client-qt',
        'wazo-doc',
        'wazo-pbx.github.io',
        'wazo-python-anytree-packaging',
        'xivo-agentd-client',
        'xivo-amid-client',
        'xivo-auth-client',
        'xivo-auth-keys',
        'xivo-blog',
        'xivo-confd-client',
        'xivo-ctid',
        'xivo-ctid-client',
        'xivo-install-cd',
        'xivo-presentations',
        'xivo-provd-client',
        'xivo-python-celery-packaging',
        'xivo-web-interface',
        'xivo-ws',
    )
)

IGNORED = set(
    (
        'nestbox-ui',
        'wazo-cpaas',
        'wazo-c4-router',
        'wazo-c4-sbc',
        'wazo-kamailio-config',
        'wazo-router-confd-poc',
        'wazo-unicom',
        'wazo-nexsis',
    )
)


class NoSuchChore(ValueError):
    def __init__(self, name):
        self.chore_name = name


class ChoreList(Command):
    def get_parser(self, *args, **kwargs):
        parser = super().get_parser(*args, **kwargs)
        parser.add_argument('--list', action='store_true', help='list chores')
        parser.add_argument('chore', nargs='?', help='a chore to detail')
        return parser

    def take_action(self, parsed_args):
        if parsed_args.list or parsed_args.chore is None:
            self.print_chores_stats()
        elif parsed_args.chore:
            chore_name = parsed_args.chore
            try:
                chore = self.get_chore(chore_name)
            except NoSuchChore as e:
                print(f'Chore not found: {e.chore_name}')
                return

            self.list_chore_details(chore)

    def all_chores(self):
        return Chore.__subclasses__()

    def get_chore(self, name):
        candidate_chores = (chore for chore in self.all_chores() if chore.name == name)
        try:
            return next(candidate_chores)
        except StopIteration:
            raise NoSuchChore(name)

    def list_chore_details(self, chore):
        for repo_name, repo_path in self.active_repos():
            if chore.is_applicable(repo_path) and chore.is_dirty(repo_path):
                chore.print_dirty_details(repo_path, repo_name)

    def print_chores_stats(self):
        for chore in self.all_chores():
            active_repos = list(repo_path for _, repo_path in self.active_repos())
            applicable_repo_paths = [
                repo_path
                for repo_path in active_repos
                if chore.is_applicable(repo_path)
            ]
            clean_repo_paths = [
                repo_path
                for repo_path in applicable_repo_paths
                if not chore.is_dirty(repo_path)
            ]
            total = len(applicable_repo_paths)
            clean = len(clean_repo_paths)
            print(f'{chore.name}:', clean, '/', total, 'OK' if clean == total else '')

    def active_repos(self):
        all_repo_names = set(
            d
            for d in os.listdir(self.config.local_source)
            if os.path.isdir(os.path.join(self.config.local_source, d))
        )
        active_repos_ = all_repo_names - ARCHIVES - IGNORED
        for repo_name in active_repos_:
            repo_path = os.path.join(self.config.local_source, repo_name)
            yield repo_name, repo_path
