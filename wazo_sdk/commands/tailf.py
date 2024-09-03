# Copyright 2019-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from typing import Any

from cliff.command import Command

from wazo_sdk.service import ServiceManager


class Tailf(Command):
    """watch the log output for a given service"""

    service: ServiceManager

    def get_parser(self, *args: Any, **kwargs: Any) -> ArgumentParser:
        parser = super().get_parser(*args, **kwargs)
        parser.add_argument('service', help='services to restart')
        return parser

    def take_action(self, parsed_args: Namespace) -> None:
        self.service.tailf(parsed_args.service)
