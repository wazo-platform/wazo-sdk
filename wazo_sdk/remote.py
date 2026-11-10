# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+
from __future__ import annotations

import shlex
from typing import TYPE_CHECKING

import sh

if TYPE_CHECKING:
    from wazo_sdk.config import Config


def rsync_shell(config: Config) -> str | None:
    args = ssh_args(config)
    return shlex.join(['ssh', *args]) if args else None


def ssh_args(config: Config) -> list[str]:
    return ['-J', config.proxy_jump] if config.proxy_jump else []


def ssh_to(config: Config) -> sh.Command:
    return sh.ssh.bake(*ssh_args(config), config.hostname)
