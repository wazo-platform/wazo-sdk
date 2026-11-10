# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from wazo_sdk.remote import rsync_shell, ssh_args


@pytest.mark.parametrize(
    ('proxy_jump', 'args', 'shell'),
    [
        (
            'alice@bastion:2200',
            ['-J', 'alice@bastion:2200'],
            'ssh -J alice@bastion:2200',
        ),
        (None, [], None),
    ],
)
def test_ssh_goes_through_the_proxy_jump(
    proxy_jump: str | None, args: list[str], shell: str | None
) -> None:
    config = MagicMock(proxy_jump=proxy_jump)

    assert (ssh_args(config), rsync_shell(config)) == (args, shell)
