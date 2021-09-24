# Copyright 2018-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import os
import subprocess

from cliff.command import Command

ARCHIVES = set((
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
))

IGNORED = set((
    'nestbox-ui',
    'wazo-cpaas',
    'wazo-c4-router',
    'wazo-c4-sbc',
    'wazo-kamailio-config',
    'wazo-router-confd-poc',
    'wazo-unicom',
    'wazo-nexsis',
))


class ChoreList(Command):

    def get_parser(self, *args, **kwargs):
        parser = super().get_parser(*args, **kwargs)
        parser.add_argument('--list', action='store_true', help='list chores')
        parser.add_argument('chore', nargs='?', help='a chore to detail')
        return parser

    def take_action(self, parsed_args):
        if parsed_args.list or parsed_args.chore is None:
            self.list_chores()
        elif parsed_args.chore == 'docker':
            self.list_docker_chore()
        elif parsed_args.chore == 'authors':
            self.list_authors_chore()

    def list_docker_chore(self):
        for repo_name, repo_path in self.active_repos():
            if has_dockerfile(repo_path) and needs_split_dockerfile(repo_path):
                print(repo_name)

    def list_authors_chore(self):
        for repo_name, repo_path in self.active_repos():
            if has_authors_file(repo_path) and not has_wazo_author(repo_path):
                print(repo_name)

    def list_chores(self):
        count = 0
        total = 0
        for repo_name, repo_path in self.active_repos():
            if has_dockerfile(repo_path):
                total += 1
                if not needs_split_dockerfile(repo_path):
                    count += 1
        print('docker:', count, '/', total, 'OK' if count == total else '')

        count = 0
        total = 0
        for repo_name, repo_path in self.active_repos():
            if has_authors_file(repo_path):
                total += 1
                if not has_wazo_author(repo_path):
                    count += 1
        print('authors:', count, '/', total, 'OK' if count == total else '')

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


def has_dockerfile(repo_path):
    return os.path.isfile(os.path.join(repo_path, 'Dockerfile'))


def needs_split_dockerfile(repo_path):
    return has_one_dockerfile_from(repo_path) and has_requirements_txt(repo_path)


def has_one_dockerfile_from(repo_path):
    try:
        return subprocess.check_output(['grep', '--ignore-case', '--count', '^FROM', os.path.join(repo_path, 'Dockerfile')]).decode('utf-8').strip() == '1'
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            return False
        raise


def has_requirements_txt(repo_path):
    command = ['grep', '--quiet', '--ignore-case', 'requirements.txt', os.path.join(repo_path, 'Dockerfile')]
    return subprocess.run(command).returncode == 0


def has_authors_file(repo_path):
    return os.path.isfile(os.path.join(repo_path, 'AUTHORS'))


def has_wazo_author(repo_path):
    command = ['grep', '--quiet', '--ignore-case', 'Wazo Communication Inc.', os.path.join(repo_path, 'AUTHORS')]
    return subprocess.run(command).returncode == 0
