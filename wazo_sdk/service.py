# Copyright 2018-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from logging import Logger

from wazo_sdk.config import Config
from wazo_sdk.remote import ssh_to


class ServiceManager:
    def __init__(self, logger: Logger, config: Config) -> None:
        self.logger = logger
        self._config = config

    def restart(self, service: str) -> None:
        project = self._config.get_project(service)
        service_name = project.service or self._config.get_project_name(service)
        ssh = ssh_to(self._config)
        ssh(f'systemctl restart {service_name}')

    def tailf(self, service: str) -> None:
        project = self._config.get_project(service)
        log_filename = project.log_filename
        if not log_filename:
            project_name = self._config.get_project_name(service)
            log_filename = f'/var/log/{project_name}.log'

        ssh = ssh_to(self._config)
        for line in ssh.tail('-f', log_filename, _iter=True):
            print(line, end='')
