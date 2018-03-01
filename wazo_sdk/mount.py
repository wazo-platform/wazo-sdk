# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+


class Mounter:

    def __init__(self, logger):
        self.logger = logger

    def mount(self, repo_name):
        self.logger.info('mounting %s', repo_name)
