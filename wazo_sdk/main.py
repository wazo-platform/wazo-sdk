# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import os
import sys
import yaml

from cliff.app import App
from cliff.commandmanager import CommandManager

from wazo_sdk.mount import Mounter

_DEFAULT_CONFIG_FILENAME = os.path.expanduser('~/.config/wdk/config.yml')
_DEFAULT_CONFIG_FILENAME = os.getenv('WDK_CONFIG_FILE', _DEFAULT_CONFIG_FILENAME)


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
        parser.add_argument('--hostname', help='The remove host when Wazo is installed')
        parser.add_argument('--dev-dir', help='Where the local source code is')
        return parser

    def initialize_app(self, argv):
        self.LOG.debug('options=%s', self.options)
        config_filename = self.options.config
        config = load_config_file(config_filename)
        self.LOG.debug('Config: %s', config)

        hostname = self.options.hostname or config.get('hostname')
        dev_dir = self.options.dev_dir or config.get('local_source')
        remote_dir = config.get('rmeote_source')

        self._mounter = Mounter(self.LOG, hostname, dev_dir, remote_dir)

    def prepare_to_run_command(self, cmd):
        cmd.mounter = self._mounter


def main(argv=sys.argv[1:]):
    app = WDK()
    return app.run(argv)
