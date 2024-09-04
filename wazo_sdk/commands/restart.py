# Copyright 2018-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from argparse import ArgumentParser, Namespace
from typing import Any

from cliff.command import Command

from wazo_sdk.service import ServiceManager


class Restart(Command):
    """restart one or more services"""

    service: ServiceManager

    def get_parser(self, *args: Any, **kwargs: Any) -> ArgumentParser:
        parser = super().get_parser(*args, **kwargs)
        parser.add_argument('services', nargs='+', help='services to restart')
        return parser

    def take_action(self, parsed_args: Namespace) -> None:
        for service_name in parsed_args.services:
            self.service.restart(service_name)
