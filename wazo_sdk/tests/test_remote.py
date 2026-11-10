# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import annotations

from unittest.mock import MagicMock

from wazo_sdk.remote import rsync_shell, ssh_args


def _config(proxy_jump: str | None) -> MagicMock:
    config = MagicMock()
    config.hostname = 'root@wazo'
    config.proxy_jump = proxy_jump
    return config


class TestSshArgs:
    def test_none_without_a_proxy_jump(self) -> None:
        assert ssh_args(_config(None)) == []

    def test_jump_through_the_proxy_jump(self) -> None:
        assert ssh_args(_config('alice@bastion:2200')) == ['-J', 'alice@bastion:2200']


class TestRsyncShell:
    def test_none_without_a_proxy_jump(self) -> None:
        assert rsync_shell(_config(None)) is None

    def test_ssh_through_the_proxy_jump(self) -> None:
        assert rsync_shell(_config('alice@bastion:2200')) == 'ssh -J alice@bastion:2200'
