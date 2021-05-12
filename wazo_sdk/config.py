# Copyright 2018-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import os
import yaml

_DEFAULT_PROJECT_FILENAME = '~/.config/wdk/project.yml'
_DEFAULT_CACHE_DIR = '~/.local/cache/wdk'
_DEFAULT_STATE_FILENAME = 'state'
REPO_PREFIX = ['', 'wazo-', 'xivo-']


class Config:

    def __init__(self, args):
        self._args = args
        self._file_config = self._read_config_file()
        self._project_config = self._read_project_file()

    @property
    def cache_dir(self):
        return os.path.expanduser(self._file_config.get('cache_dir', _DEFAULT_CACHE_DIR))

    @property
    def hostname(self):
        return self._args.hostname or self._file_config.get('hostname')

    @property
    def rsync_only(self):
        return self._args.rsync_only or self._file_config.get('rsync_only') or False

    @property
    def local_source(self):
        local_source = self._args.dev_dir or self._file_config.get('local_source')
        if not local_source:
            raise Exception("Unable to find local source")
        return os.path.expanduser(local_source)

    @property
    def remote_source(self):
        return self._file_config.get('remote_source')

    @property
    def state_file_path(self):
        return os.path.join(self.cache_dir, _DEFAULT_STATE_FILENAME)

    @property
    def project_file(self):
        return os.path.expanduser(
            self._args.project_file
            or os.getenv('WDK_PROJECT_FILE')
            or self._file_config.get('project_file')
            or _DEFAULT_PROJECT_FILENAME
        )

    @property
    def github_orgs(self):
        return self._file_config.get('github_orgs')

    @property
    def github_token(self):
        return self._file_config.get('github_token')

    @property
    def github_username(self):
        return self._file_config.get('github_username')

    def get_project(self, short_name):
        name = self.get_project_name(short_name)
        return self._project_config[name]

    def get_project_name(self, short_name):
        for prefix in REPO_PREFIX:
            name = '{}{}'.format(prefix, short_name)
            if name in self._project_config:
                return name

        raise Exception('No such project {}'.format(short_name))

    def _read_config_file(self):
        filename = os.path.expanduser(self._args.config)
        return self._read_yml_file(filename)

    def _read_project_file(self):
        return self._read_yml_file(self.project_file)

    def _read_yml_file(self, filename):
        try:
            return yaml.safe_load(open(filename, 'r'))
        except IOError:
            return {}
