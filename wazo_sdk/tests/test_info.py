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


def _info(tmp_path: pathlib.Path, config_yaml: str) -> Info:
    config_file = tmp_path / 'config.yml'
    config_file.write_text(config_yaml)
    project_file = tmp_path / 'project.yml'
    project_file.write_text('{}\n')
    config = Config(
        Namespace(
            config=str(config_file),
            project_file=str(project_file),
            hostname=None,
            dev_dir=str(tmp_path),
            rsync_only=False,
            proxy_jump=None,
        )
    )
    info = Info(MagicMock(), Namespace())
    info.service = ServiceManager(MagicMock(), config)
    return info


@pytest.mark.parametrize(
    ('config_yaml', 'shown'),
    [('proxy_jump: alice@bastion:2200\n', 'alice@bastion:2200'), ('{}\n', 'None')],
)
def test_info_shows_the_proxy_jump(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    config_yaml: str,
    shown: str,
) -> None:
    _info(tmp_path, config_yaml).take_action(Namespace())

    assert f'proxy_jump: {shown}' in capsys.readouterr().out.splitlines()
