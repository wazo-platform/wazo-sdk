# Copyright 2018-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import annotations

import logging
from argparse import ArgumentParser, Namespace
from typing import Any

from cliff.command import Command

from wazo_sdk.mount import Mounter
from wazo_sdk.service import ServiceManager


class Mount(Command):
    """mount one or more services on a remote instance"""

    mounter: Mounter
    service: ServiceManager

    def get_parser(self, *args: Any, **kwargs: Any) -> ArgumentParser:
        parser = super().get_parser(*args, **kwargs)
        parser.add_argument(
            '--list', action='store_true', help='list mounted repositories'
        )
        parser.add_argument(
            '--restart', '-r', action='store_true', help='restart mounted repositories'
        )
        parser.add_argument(
            'repos',
            nargs='*',
            default=[],
            help=(
                'a list of repos to mount; '
                'use <repo>=<path> to mount a checkout outside the dev directory'
            ),
        )
        return parser

    def take_action(self, parsed_args: Namespace) -> None:
        for spec in parsed_args.repos:
            repo, _, local_path = spec.partition('=')
            try:
                self.mounter.mount(repo, local_path or None)
            except Exception:
                self.app.LOG.exception('Error mount repo %s', repo)
            else:
                if parsed_args.restart:
                    try:
                        self.service.restart(repo)
                    except Exception:
                        self.app.LOG.exception('Error restarting repo %s', repo)

        if parsed_args.list:
            mounted_repos = self.mounter.list_()
            for repo, running, local_path in mounted_repos:
                state = 'UP' if running else 'DOWN'
                if local_path:
                    self.app.LOG.info('%s %s %s', repo, state, local_path)
                else:
                    self.app.LOG.info('%s %s', repo, state)


class Umount(Command):
    """umount one or more services from a remote instance"""

    mounter: Mounter
    service: ServiceManager
    logger = logging.getLogger(__name__)

    def get_parser(self, *args: Any, **kwargs: Any) -> ArgumentParser:
        parser = super().get_parser(*args, **kwargs)
        parser.add_argument(
            'repos', nargs='*', default=[], help='a list repos to unmount'
        )
        parser.add_argument(
            '--restart',
            '-r',
            action='store_true',
            help='restart unmounted repositories',
        )
        return parser

    def take_action(self, parsed_args: Namespace) -> None:
        specs = parsed_args.repos or [repo for repo, _, _ in self.mounter.list_()]
        for spec in specs:
            # tolerate the <repo>=<path> form accepted by mount
            repo = spec.partition('=')[0]
            try:
                self.mounter.umount(repo)
            except Exception:
                self.app.LOG.exception('Error unmount repo %s', repo)
            else:
                if parsed_args.restart:
                    try:
                        self.service.restart(repo)
                    except Exception:
                        self.app.LOG.exception('Error restarting repo %s', repo)
