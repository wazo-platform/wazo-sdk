# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import sys

from cliff.app import App
from cliff.commandmanager import CommandManager

from wazo_sdk.mount import Mounter


class WDK(App):

    def __init__(self):
        super().__init__(
            description='Wazo SDK',
            command_manager=CommandManager('wazo_sdk.commands'),
            version='0.0.1',
        )
        self._mounter = Mounter(self.LOG)

    def prepare_to_run_command(self, cmd):
        cmd.mounter = self._mounter


def main(argv=sys.argv[1:]):
    app = WDK()
    return app.run(argv)
