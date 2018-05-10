# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import json


class State:

    def __init__(self, data):
        self._data = data

    def add_mount(self, host, repo, config, pid):
        mount = {
            'project': repo,
            'lsync_config': config,
            'lsync_pidfile': pid,
        }
        self.get_mounts(host)[repo] = mount

    def get_mount(self, host, repo):
        return self._nested_get('hosts', host, 'mounts', repo)

    def get_mounts(self, host):
        return self._nested_get('hosts', host, 'mounts')

    def is_mounted(self, host, repo):
        mount = self.get_mount(host, repo)
        return True if mount else False

    def remove_mount(self, host, repo):
        mounts = self._data['hosts'][host]['mounts']
        if not mounts:
            return

        if repo not in mounts:
            return

        del mounts[repo]

    def to_file(self, f):
        return json.dump(self._data, f)

    @classmethod
    def from_json(cls, json):
        return cls(json)

    @classmethod
    def from_file(cls, f):
        return cls.from_json(json.load(f))

    def _nested_get(self, *keys):
        data = self._data
        for key in keys:
            data = data.get(key, {})

        return data
