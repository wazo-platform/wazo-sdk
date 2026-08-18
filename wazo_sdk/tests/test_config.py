# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import annotations

import pathlib
from argparse import Namespace

import pytest

from wazo_sdk.config import Config, Project, ProjectConfigError


def _make_config(tmp_path: pathlib.Path, project_yaml: str) -> Config:
    project_file = tmp_path / 'project.yml'
    project_file.write_text(project_yaml)
    config_file = tmp_path / 'config.yml'
    config_file.write_text('{}\n')

    args = Namespace(
        config=str(config_file),
        project_file=str(project_file),
        hostname=None,
        dev_dir=None,
        rsync_only=False,
    )
    return Config(args)


class TestProject:
    def test_defaults(self) -> None:
        project = Project(name='wazo-foo')

        assert project.python3 is False
        assert project.bind == {}
        assert project.clean == []

    def test_raises_when_bind_is_not_a_mapping(self) -> None:
        # Missing space after the colon folds this block into a single
        # scalar string instead of a YAML mapping.
        with pytest.raises(ProjectConfigError, match='bind'):
            Project(name='wazo-foo', bind='etc/foo.yml:/etc/foo.yml')  # type: ignore[arg-type]

    def test_raises_when_clean_is_not_a_list(self) -> None:
        with pytest.raises(ProjectConfigError, match='clean'):
            Project(name='wazo-foo', clean='/usr/local/bin/wazo-foo')  # type: ignore[arg-type]


class TestGetProject:
    def test_returns_project(self, tmp_path: pathlib.Path) -> None:
        config = _make_config(
            tmp_path,
            'wazo-foo:\n'
            '  python3: true\n'
            '  bind:\n'
            '    etc/foo.yml: /etc/foo.yml\n',
        )

        project = config.get_project('wazo-foo')

        assert project.bind == {'etc/foo.yml': '/etc/foo.yml'}

    def test_bare_project_entry_uses_defaults(self, tmp_path: pathlib.Path) -> None:
        config = _make_config(tmp_path, 'wazo-foo:\n')

        project = config.get_project('wazo-foo')

        assert project.bind == {}
        assert project.clean == []
        assert project.python3 is False

    def test_raises_explicit_error_when_bind_is_not_a_mapping(
        self, tmp_path: pathlib.Path
    ) -> None:
        config = _make_config(
            tmp_path,
            'wazo-foo:\n'
            '  python3: true\n'
            '  bind:\n'
            '    etc/foo.yml:/etc/foo.yml\n',
        )

        with pytest.raises(ProjectConfigError, match='bind'):
            config.get_project('wazo-foo')

    def test_raises_explicit_error_when_clean_is_not_a_list(
        self, tmp_path: pathlib.Path
    ) -> None:
        config = _make_config(
            tmp_path, 'wazo-foo:\n' '  clean: /usr/local/bin/wazo-foo\n'
        )

        with pytest.raises(ProjectConfigError, match='clean'):
            config.get_project('wazo-foo')

    def test_raises_explicit_error_when_project_is_not_a_mapping(
        self, tmp_path: pathlib.Path
    ) -> None:
        config = _make_config(tmp_path, 'wazo-foo: true\n')

        with pytest.raises(ProjectConfigError, match='wazo-foo'):
            config.get_project('wazo-foo')

    def test_raises_explicit_error_on_unknown_key(self, tmp_path: pathlib.Path) -> None:
        config = _make_config(tmp_path, 'wazo-foo:\n' '  unknown_field: 1\n')

        with pytest.raises(ProjectConfigError, match='wazo-foo'):
            config.get_project('wazo-foo')

    def test_error_message_includes_project_file_path(
        self, tmp_path: pathlib.Path
    ) -> None:
        config = _make_config(
            tmp_path, 'wazo-foo:\n' '  bind:\n' '    etc/foo.yml:/etc/foo.yml\n'
        )

        with pytest.raises(ProjectConfigError, match=str(tmp_path / 'project.yml')):
            config.get_project('wazo-foo')
