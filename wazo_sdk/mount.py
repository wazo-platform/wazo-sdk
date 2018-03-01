# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import os


class Mounter:

    def __init__(self, logger, hostname, local_dir):
        self.logger = logger
        self._hostname = hostname
        self._local_dir = local_dir

    def mount(self, repo_name):
        if not self._hostname:
            raise Exception('The remote hostname is required to mount directories')

        if not self._local_dir:
            raise Exception('The local source directory is required to mount directories')

        repo_path = os.path.join(self._local_dir, repo_name)
        self.logger.info('mounting %s on %s', repo_path, self._hostname)
