# Copyright 2018-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+
from __future__ import annotations

import json
from typing import Any, TextIO, TYPE_CHECKING


if TYPE_CHECKING:
    from typing import TypedDict

    class MountData(TypedDict):
        project: str
        lsync_config: str | None
        lsync_pidfile: str | None


class State:
    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self._data = data or {'hosts': {}}

    def add_mount(
        self, host: str, repo: str, config: str | None, pid: str | None
    ) -> None:
        mount: MountData = {
            'project': repo,
            'lsync_config': config,
            'lsync_pidfile': pid,
        }
        self.get_mounts(host)[repo] = mount

    def get_mount(self, host: str, repo: str) -> MountData:
        return self._nested_get('hosts', host, 'mounts', repo)  # type: ignore

    def get_mounts(self, host: str) -> dict[str, MountData]:
        mounts: dict[str, MountData] = self._nested_get('hosts', host, 'mounts')
        return mounts

    def is_mounted(self, host: str, repo: str) -> bool:
        mount = self.get_mount(host, repo)
        return bool(mount)

    def remove_mount(self, host: str, repo: str) -> None:
        mounts = self._data['hosts'][host]['mounts']
        if not mounts:
            return

        if repo not in mounts:
            return

        del mounts[repo]

    def to_file(self, f: TextIO) -> None:
        return json.dump(self._data, f)

    @classmethod
    def from_json(cls, json: dict[str, Any]) -> State:
        return cls(json)

    @classmethod
    def from_file(cls, f: TextIO) -> State:
        return cls.from_json(json.load(f))

    def _nested_get(self, *keys: str) -> dict[str, Any]:
        data = self._data
        for key in keys:
            if key not in data:
                data[key] = {}
            data = data[key]
        return data
