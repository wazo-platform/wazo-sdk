# Copyright 2019-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+
from __future__ import annotations

import json
from argparse import ArgumentParser, Namespace
from typing import Any

from cliff.command import Command
from wazo_websocketd_client import Client

from wazo_sdk.service import ServiceManager


class TailWebsocket(Command):
    """Watch the wazo event stream exposed by websocketd"""

    service: ServiceManager

    def get_parser(self, *args: Any, **kwargs: Any) -> ArgumentParser:
        parser = super().get_parser(*args, **kwargs)
        parser.add_argument(
            '--events', '-e', help='events to subscribe to', type=str, default='*'
        )
        return parser

    def take_action(self, parsed_args: Namespace) -> None:
        events = parsed_args.events.split(',')
        config = self.service._config
        host = config.hostname
        token = self.service.authenticate()

        c = Client(
            host,
            token=token['token'],
            verify_certificate=False,
            debug=self.app_args.debug,
        )

        def callback(data: dict[str, Any]) -> None:
            print(json.dumps(data), flush=True)

        if '*' in events:
            c.on('*', callback)
        else:
            for event in events:
                c.on(event, callback)

        c.run()
