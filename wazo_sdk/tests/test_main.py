# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import annotations

import os
import pathlib
from unittest.mock import MagicMock

from wazo_sdk.main import WDK


def _wdk_with_cache_dir(cache_dir: str) -> WDK:
    app = WDK.__new__(WDK)
    app.config = MagicMock()
    app.config.cache_dir = cache_dir
    app.config.state_file_path = os.path.join(cache_dir, 'state')
    app.LOG = MagicMock()
    return app


class TestRemoveStaleConfigFiles:
    def test_removes_config_file_without_pidfile(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / 'orphan_config').write_text('sync {}')
        app = _wdk_with_cache_dir(str(tmp_path))

        app._remove_stale_config_files()

        assert not (tmp_path / 'orphan_config').exists()

    def test_keeps_config_and_pidfile_pair_when_pid_alive(
        self, tmp_path: pathlib.Path
    ) -> None:
        (tmp_path / 'live_config').write_text('sync {}')
        (tmp_path / 'live_config.pid').write_text('123')
        app = _wdk_with_cache_dir(str(tmp_path))
        app._is_lsyncd_pidfile_live = MagicMock(return_value=True)  # type: ignore[method-assign]

        app._remove_stale_config_files()

        assert (tmp_path / 'live_config').exists()
        assert (tmp_path / 'live_config.pid').exists()

    def test_keeps_filter_file_when_its_config_pidfile_is_alive(
        self, tmp_path: pathlib.Path
    ) -> None:
        (tmp_path / 'live_config').write_text('sync {}')
        (tmp_path / 'live_config.pid').write_text('123')
        (tmp_path / 'live_config.filter').write_text('- .git\n')
        app = _wdk_with_cache_dir(str(tmp_path))
        app._is_lsyncd_pidfile_live = MagicMock(return_value=True)  # type: ignore[method-assign]

        app._remove_stale_config_files()

        assert (tmp_path / 'live_config.filter').exists()

    def test_removes_filter_file_when_its_config_pidfile_is_missing(
        self, tmp_path: pathlib.Path
    ) -> None:
        (tmp_path / 'orphan_config.filter').write_text('- .git\n')
        app = _wdk_with_cache_dir(str(tmp_path))

        app._remove_stale_config_files()

        assert not (tmp_path / 'orphan_config.filter').exists()

    def test_never_removes_state_file(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / 'state').write_text('{}')
        app = _wdk_with_cache_dir(str(tmp_path))

        app._remove_stale_config_files()

        assert (tmp_path / 'state').exists()

    def test_removes_pidfile_when_process_not_alive(
        self, tmp_path: pathlib.Path
    ) -> None:
        (tmp_path / 'dead_config').write_text('sync {}')
        (tmp_path / 'dead_config.pid').write_text('999999')
        app = _wdk_with_cache_dir(str(tmp_path))
        app._is_lsyncd_pidfile_live = MagicMock(return_value=False)  # type: ignore[method-assign]

        app._remove_stale_config_files()

        assert not (tmp_path / 'dead_config.pid').exists()
