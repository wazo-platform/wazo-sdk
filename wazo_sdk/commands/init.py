# Copyright 2018-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+
from __future__ import annotations

import logging
from argparse import ArgumentParser, Namespace
from typing import Any

import sh
from cliff.app import App
from cliff.command import Command

from wazo_sdk.config import Config


class PackageManager:
    hostname: str

    def __init__(self, hostname: str, logger: logging.Logger) -> None:
        self.hostname = hostname
        self.logger = logger

    def ensure_packages(self, packages: list[str]):
        if packages:
            ssh = sh.ssh.bake(self.hostname, _return_cmd=True)
            self._install_packages(ssh, packages)

            yield from self._check_packages(ssh, packages)

    def _check_packages(self, ssh: sh.Command, packages: list[str]):
        for pkg in packages:
            run_cmd: sh.RunningCommand = ssh(f'apt-cache policy {pkg}')
            # try:
            # except sh.ErrorReturnCode as ex:
            #     success = False
            self.logger.debug('cmd=%s', run_cmd)

            yield {
                'success': (
                    run_cmd.exit_code == 0 and pkg in run_cmd.stdout.decode('utf-8')
                ),
                'details': run_cmd.stdout.decode('utf-8'),
                'name': pkg,
            }

    def _install_packages(self, ssh: sh.Command, packages: list[str]) -> None:
        # setup_path = os.path.join(self._remote_dir, repo_name, 'setup.py')
        # self._wait_for_file(ssh, setup_path)

        # repo_dir = os.path.join(self._remote_dir, repo_name)
        cmd = ['apt-get', 'update', '&&', 'apt-get', 'install', '-y', *packages]
        run_cmd: sh.RunningCommand = ssh(' '.join(cmd))
        self.logger.debug("install command: %s", run_cmd)
        self.logger.debug("install command output: %s", run_cmd.stdout)
        return run_cmd


class Init(Command):
    """Prepare remote target system for wdk integration"""

    # package_manager: PackageManager
    config: Config
    logger = logging.getLogger(__name__)
    app: App

    def get_parser(self, *args: Any, **kwargs: Any) -> ArgumentParser:
        parser = super().get_parser(*args, **kwargs)
        # parser.add_argument(
        #     '--list', action='store_true', help='list mounted repositories'
        # )
        # parser.add_argument(
        #     '--restart', '-r', action='store_true', help='restart mounted repositories'
        # )
        # parser.add_argument(
        #     'repos', nargs='*', default=[], help='a list repos to mount'
        # )
        return parser

    def take_action(self, parsed_args: Namespace) -> None:
        package_manager = PackageManager(self.config.hostname, self.logger)
        if not self.config.init_packages:
            self.app.stdout.write('no packages to install\n')
            return
        self.app.stdout.write(
            f'installing packages in stack environment: {self.config.init_packages}\n'
        )
        for pkg in package_manager.ensure_packages(self.config.init_packages):
            if pkg['success']:
                self.app.stdout.write(f'package {pkg["name"]} successfully installed\n')
                if self.app.options.verbose_level > 1 or self.app.options.debug:
                    self.app.stderr.write(pkg['details'] + '\n')
            else:
                self.app.stdout.write(f'package {pkg["name"]} installation failed\n')
                self.app.stderr.write(pkg["details"] + '\n')
