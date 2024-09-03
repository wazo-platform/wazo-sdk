# Copyright 2018-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from argparse import Namespace

from cliff.command import Command

from wazo_sdk.service import ServiceManager


class Info(Command):
    """print WDK config information"""

    service: ServiceManager

    def take_action(self, parsed_args: Namespace) -> None:
        service_config = self.service._config
        print(f'hostname: {service_config.hostname}')
        print(f'project_file: {service_config.project_file}')
        print(f'config_file: {service_config._args.config}')
        print(f'local_source: {service_config.local_source}')
        print(f'remote_source: {service_config.remote_source}')
        print(f'cache_dir: {service_config.cache_dir}')
        print(f'state_file_path: {service_config.state_file_path}')
