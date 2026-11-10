# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import annotations

from argparse import Namespace
from unittest.mock import MagicMock

import pytest

from wazo_sdk.commands.info import Info


@pytest.mark.parametrize('proxy_jump', ['alice@bastion:2200', None])
def test_info_shows_the_proxy_jump(
    capsys: pytest.CaptureFixture[str], proxy_jump: str | None
) -> None:
    info = Info(MagicMock(), Namespace())
    info.service = MagicMock()
    info.service._config.proxy_jump = proxy_jump

    info.take_action(Namespace())

    assert f'proxy_jump: {proxy_jump}' in capsys.readouterr().out.splitlines()
