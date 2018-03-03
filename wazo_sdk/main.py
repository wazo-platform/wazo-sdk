# Copyright 2017-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import os
import sys
import yaml

from cliff.app import App
from cliff.commandmanager import CommandManager

from wazo_sdk.mount import Mounter

_DEFAULT_CONFIG_FILENAME = os.path.expanduser('~/.config/wdk/config.yml')
_DEFAULT_CONFIG_FILENAME = os.getenv('WDK_CONFIG_FILE', _DEFAULT_CONFIG_FILENAME)
_DEFAULT_PROJECT_FILENAME = '~/.config/wdk/project.yml'


def load_config_file(filename):
    try:
        return yaml.load(open(filename, 'r'))
    except IOError:
        return {}


class WDK(App):

    def __init__(self):
        super().__init__(
            description='Wazo SDK',
            command_manager=CommandManager('wazo_sdk.commands'),
            version='0.0.1',
        )

    def build_option_parser(self, *args, **kwargs):
        parser = super().build_option_parser(*args, **kwargs)
        parser.add_argument('--config', default=_DEFAULT_CONFIG_FILENAME,
                            help='Configuration file name')
        parser.add_argument('--project-file', help='Project description file', default=None)
        parser.add_argument('--hostname', help='The remove host when Wazo is installed')
        parser.add_argument('--dev-dir', help='Where the local source code is')
        return parser

    def initialize_app(self, argv):
        self.LOG.debug('options=%s', self.options)
        config_filename = self.options.config
        config = load_config_file(config_filename)
        relative_project_filename = \
            self.options.project_file \
            or os.getenv('WDK_PROJECT_FILE') \
            or config.get('project_file') \
            or _DEFAULT_PROJECT_FILENAME
        project_filename = os.path.expanduser(relative_project_filename)
        project_config = load_config_file(project_filename)
        self.LOG.debug('Config: %s', config)
        self.LOG.debug('Projects: %s', project_config)

        hostname = self.options.hostname or config.get('hostname')
        dev_dir = os.path.expanduser(self.options.dev_dir or config.get('local_source'))
        remote_dir = config.get('remote_source')

        self._mounter = Mounter(self.LOG, hostname, dev_dir, remote_dir, project_config)

    def prepare_to_run_command(self, cmd):
        cmd.mounter = self._mounter


def main(argv=sys.argv[1:]):
    app = WDK()
    return app.run(argv)
