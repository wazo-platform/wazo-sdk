# Copyright 2018-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from logging import Logger

import sh

from wazo_sdk.config import Config


class ServiceManager:
    def __init__(self, logger: Logger, config: Config) -> None:
        self.logger = logger
        self._config = config

    def restart(self, service: str) -> None:
        project = self._config.get_project(service)
        service_name = project.get('service', self._config.get_project_name(service))
        ssh = sh.ssh.bake(self._config.hostname)
        ssh(f'systemctl restart {service_name}')

    def tailf(self, service: str) -> None:
        project = self._config.get_project(service)
        log_filename = project.get('log_filename')
        if not log_filename:
            project_name = self._config.get_project_name(service)
            log_filename = f'/var/log/{project_name}.log'

        ssh = sh.ssh.bake(self._config.hostname)
        for line in ssh.tail('-f', log_filename, _iter=True):
            print(line, end='')
