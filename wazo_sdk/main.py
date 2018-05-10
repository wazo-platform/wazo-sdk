# Copyright 2017-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import json
import os
import sys
import pathlib

from cliff.app import App
from cliff.commandmanager import CommandManager

from wazo_sdk.config import Config
from wazo_sdk.mount import Mounter
from wazo_sdk.service import ServiceManager

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
        self.config = Config(self.options)

        self._create_cache_dir(self.config.cache_dir)

        try:
            with open(self.config.state_file_path, 'r') as f:
                self.state = json.load(f) or {}
        except IOError:
            self.state = {}

        if 'hosts' not in self.state:
            self.state['hosts'] = {}

        self._service_manager = ServiceManager(self.LOG, self.config)
        self._mounter = Mounter(self.LOG, self.config, self.state)

    def prepare_to_run_command(self, cmd):
        cmd.mounter = self._mounter
        cmd.service = self._service_manager

    def clean_up(self, cmd, result, err):
        if err:
            return

        with open(self.config.state_file_path, 'w') as f:
            json.dump(self.state, f)

    def _create_cache_dir(self, path):
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def main(argv=sys.argv[1:]):
    app = WDK()
    return app.run(argv)
