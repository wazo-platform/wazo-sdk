# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import os
import subprocess

REPO_PREFIX = ['', 'wazo-', 'xivo-']


class Mounter:

    def __init__(self, logger, hostname, local_dir):
        self.logger = logger
        self._hostname = hostname
        self._local_dir = local_dir
        # TODO: make this configurable
        self._remote_dir = '/root/dev/wazo'

    def mount(self, repo_name):
        if not self._hostname:
            raise Exception('The remote hostname is required to mount directories')

        if not self._local_dir:
            raise Exception('The local source directory is required to mount directories')

        complete_repo_name = self._find_complete_repo_name(repo_name)

        self._start_sync(complete_repo_name)

    def _start_sync(self, repo_name):
        local_path = os.path.join(self._local_dir, repo_name)
        remote_path = os.path.join(self._remote_dir, repo_name)

        lsync_command = ['lsyncd', '-delay', '1', '-rsyncssh', local_path, self._hostname, remote_path]

        self.logger.debug('%s', ' '.join(lsync_command))
        ret = subprocess.call(lsync_command)
        if ret:
            self.logger.info('%s failed %s', ' '.join(lsync_command), ret)

    def _find_complete_repo_name(self, repo_name):
        for prefix in REPO_PREFIX:
            basename = '{}{}'.format(prefix, repo_name)
            path = os.path.join(self._local_dir, basename)
            if os.path.exists(path):
                return basename

        raise Exception('No such repo {}'.format(repo_name))
