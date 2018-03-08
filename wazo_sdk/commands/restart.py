# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from cliff.command import Command


class Restart(Command):

    def get_parser(self, *args, **kwargs):
        parser = super().get_parser(*args, **kwargs)
        parser.add_argument('services', nargs='+', help='services to restart')
        return parser

    def take_action(self, parsed_args):
        for service_name in parsed_args.services:
            self.service.restart(service_name)
