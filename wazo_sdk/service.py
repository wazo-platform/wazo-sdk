# Copyright 2018-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import sh


class ServiceManager:

    def __init__(self, logger, config):
        self.logger = logger
        self._config = config

    def restart(self, service):
        project = self._config.get_project(service)
        service_name = project.get('service', service)
        ssh = sh.ssh.bake(self._config.hostname)
        ssh('systemctl restart {}'.format(service_name))

    def tailf(self, service):
        project = self._config.get_project(service)
        log_filename = project.get('log_filename')
        if not log_filename:
            project_name = self._config.get_project_name(service)
            log_filename = '/var/log/{}.log'.format(project_name)

        ssh = sh.ssh.bake(self._config.hostname)
        for line in ssh.tail('-f', log_filename, _iter=True):
            print(line, end='')
