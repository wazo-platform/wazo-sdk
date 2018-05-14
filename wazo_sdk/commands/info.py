# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from cliff.command import Command


class Info(Command):

    def take_action(self, parsed_args):
        print('hostname: {}'.format(self.service._config.hostname))
        print('project_file: {}'.format(self.service._config.project_file))
        print('config_file: {}'.format(self.service._config._args.config))
        print('local_source: {}'.format(self.service._config.local_source))
        print('remote_source: {}'.format(self.service._config.remote_source))
        print('cache_dir: {}'.format(self.service._config.cache_dir))
        print('state_file_path: {}'.format(self.service._config.state_file_path))
