# Copyright 2018-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import annotations

import os
from argparse import Namespace
from typing import TYPE_CHECKING, Any

import yaml

_DEFAULT_PROJECT_FILENAME = '~/.config/wdk/project.yml'
_DEFAULT_CACHE_DIR = '~/.local/cache/wdk'
_DEFAULT_STATE_FILENAME = 'state'
REPO_PREFIX = ['', 'wazo-', 'xivo-']
DEFAULT_INIT_PACKAGES = ['python3-pip', 'rsync']

if TYPE_CHECKING:
    from typing import TypedDict

    class InitConfigData(TypedDict):
        packages: list[str]

    class ConfigData(TypedDict):
        hostname: str
        local_source: str
        remote_source: str
        project_file: str
        cache_dir: str
        archive_dir: str
        rsync_only: bool
        github_username: str | None
        github_token: str | None
        github_orgs: list[str]
        init: InitConfigData

    class ProjectConfigData(TypedDict):
        python2: bool
        python3: bool
        log_filename: str | None
        service: str | None
        clean: list[str]
        bind: dict[str, str]


class Config:
    def __init__(self, args: Namespace) -> None:
        self._args = args
        self._file_config = self._read_config_file()
        self._project_config = self._read_project_file()

    @property
    def cache_dir(self) -> str:
        return os.path.expanduser(
            self._file_config.get('cache_dir', _DEFAULT_CACHE_DIR)
        )

    @property
    def archive_dir(self) -> str:
        return os.path.expanduser(
            self._file_config.get('archive_dir', self.local_source)
        )

    @property
    def hostname(self) -> str | None:
        return self._args.hostname or self._file_config.get('hostname')

    @property
    def rsync_only(self) -> bool:
        return self._args.rsync_only or self._file_config.get('rsync_only') or False

    @property
    def local_source(self) -> str:
        local_source = self._args.dev_dir or self._file_config.get('local_source')
        if not local_source:
            raise Exception("Unable to find local source")
        return os.path.expanduser(local_source)

    @property
    def remote_source(self) -> str | None:
        return self._file_config.get('remote_source')

    @property
    def state_file_path(self) -> str:
        return os.path.join(self.cache_dir, _DEFAULT_STATE_FILENAME)

    @property
    def project_file(self) -> str:
        return os.path.expanduser(
            self._args.project_file
            or os.getenv('WDK_PROJECT_FILE')
            or self._file_config.get('project_file')
            or _DEFAULT_PROJECT_FILENAME
        )

    @property
    def github_orgs(self) -> list[str]:
        return self._file_config.get('github_orgs') or []

    @property
    def github_token(self) -> str | None:
        return self._file_config.get('github_token')

    @property
    def github_username(self) -> str | None:
        return self._file_config.get('github_username')

    @property
    def init_packages(self) -> list[str]:
        return self._file_config.get('init', {}).get('packages', DEFAULT_INIT_PACKAGES)

    def get_project(self, short_name: str) -> ProjectConfigData:
        name = self.get_project_name(short_name)
        return self._project_config[name]

    def get_project_name(self, short_name: str) -> str:
        for prefix in REPO_PREFIX:
            name = f'{prefix}{short_name}'
            if name in self._project_config:
                return name

        raise Exception(f'No such project {short_name}')

    def _read_config_file(self) -> ConfigData:
        filename = os.path.expanduser(self._args.config)
        return self._read_yml_file(filename)  # type: ignore

    def _read_project_file(self) -> dict[str, ProjectConfigData]:
        return self._read_yml_file(self.project_file)

    def _read_yml_file(self, filename: str) -> dict[str, Any]:
        try:
            with open(filename) as f:
                return yaml.safe_load(f)
        except OSError:
            return {}
