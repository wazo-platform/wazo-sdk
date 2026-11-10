# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+
from __future__ import annotations

from typing import TYPE_CHECKING

import sh

if TYPE_CHECKING:
    from wazo_sdk.config import Config


def rsync_shell(config: Config) -> str | None:
    if not config.proxy_jump:
        return None
    return f'ssh -J {config.proxy_jump}'


def ssh_to(config: Config) -> sh.Command:
    jump = ['-J', config.proxy_jump] if config.proxy_jump else []
    return sh.ssh.bake(*jump, config.hostname)
