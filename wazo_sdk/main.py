# Copyright 2017-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import os
import sys

from cliff.app import App
from cliff.commandmanager import CommandManager

from wazo_sdk.config import Config
from wazo_sdk.mount import Mounter

_DEFAULT_CONFIG_FILENAME = os.path.expanduser('~/.config/wdk/config.yml')
_DEFAULT_CONFIG_FILENAME = os.getenv('WDK_CONFIG_FILE', _DEFAULT_CONFIG_FILENAME)


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
        parser.add_argument('--project-file', help='Project configuration file', default=None)
        parser.add_argument('--hostname', help='The remote host when Wazo is installed')
        parser.add_argument('--dev-dir', help='Where the local source code is')
        return parser

    def initialize_app(self, argv):
        config = Config(self.options)
        self._mounter = Mounter(self.LOG, config)

    def prepare_to_run_command(self, cmd):
        cmd.mounter = self._mounter


def main(argv=sys.argv[1:]):
    app = WDK()
    return app.run(argv)
