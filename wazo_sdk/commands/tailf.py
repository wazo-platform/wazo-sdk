# Copyright 2019-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from cliff.command import Command


class Tailf(Command):
    def get_parser(self, *args, **kwargs):
        parser = super().get_parser(*args, **kwargs)
        parser.add_argument('service', help='services to restart')
        return parser

    def take_action(self, parsed_args):
        self.service.tailf(parsed_args.service)
