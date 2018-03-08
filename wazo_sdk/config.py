# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import os
import yaml

_DEFAULT_PROJECT_FILENAME = '~/.config/wdk/project.yml'
REPO_PREFIX = ['', 'wazo-', 'xivo-']


class Config:

    def __init__(self, args):
        self._args = args
        self._file_config = self._read_config_file()
        self._project_config = self._read_project_file()

    @property
    def hostname(self):
        return self._args.hostname or self._file_config.get('hostname')

    @property
    def local_source(self):
        return os.path.expanduser(
            self._args.dev_dir or self._file_config.get('local_source')
        )

    @property
    def remote_source(self):
        return self._file_config.get('remote_source')

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
        filename = os.path.expanduser(
            self._args.project_file
            or os.getenv('WDK_PROJECT_FILE')
            or self._file_config.get('project_file')
            or _DEFAULT_PROJECT_FILENAME
        )
        return self._read_yml_file(filename)

    def _read_yml_file(self, filename):
        try:
            return yaml.load(open(filename, 'r'))
        except IOError:
            return {}
