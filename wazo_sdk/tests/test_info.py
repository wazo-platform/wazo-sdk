# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import annotations

import pathlib
from argparse import Namespace
from unittest.mock import MagicMock

import pytest

from wazo_sdk.commands.info import Info
from wazo_sdk.config import Config
from wazo_sdk.service import ServiceManager


def test_info_shows_the_proxy_jump(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / 'config.yml').write_text('proxy_jump: alice@bastion:2200\n')
    (tmp_path / 'project.yml').write_text('{}\n')
    args = Namespace(
        config=str(tmp_path / 'config.yml'),
        project_file=str(tmp_path / 'project.yml'),
        hostname=None,
        dev_dir=str(tmp_path),
        rsync_only=False,
        proxy_jump=None,
    )
    info = Info(MagicMock(), Namespace())
    info.service = ServiceManager(MagicMock(), Config(args))

    info.take_action(Namespace())

    assert 'proxy_jump: alice@bastion:2200' in capsys.readouterr().out.splitlines()
