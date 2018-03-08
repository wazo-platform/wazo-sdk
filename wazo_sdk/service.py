# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import sh


class ServiceManager:

    def __init__(self, logger, config):
        self.logger = logger
        self._config = config

    def restart(self, service):
        service_name = self._config.get_project_name(service)
        ssh = sh.ssh.bake(self._config.hostname)
        ssh('systemctl restart {}'.format(service_name))
