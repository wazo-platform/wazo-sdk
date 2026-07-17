# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import annotations

import io
import pathlib

from wazo_sdk.gitignore import (
    _read_ignore_file,
    _read_ignore_lines,
    gitignore_exclude_rules,
)


class TestReadIgnoreLines:
    def test_skips_blank_lines(self) -> None:
        assert _read_ignore_lines(io.StringIO('a\n\nb\n   \nc\n')) == ['a', 'b', 'c']

    def test_skips_comment_lines(self) -> None:
        stream = io.StringIO('# a comment\na\n; another comment\nb\n')

        assert _read_ignore_lines(stream) == ['a', 'b']

    def test_preserves_negation_prefix(self) -> None:
        stream = io.StringIO('build/*\n!build/keep.txt\n')

        assert _read_ignore_lines(stream) == ['build/*', '!build/keep.txt']

    def test_empty_stream(self) -> None:
        assert _read_ignore_lines(io.StringIO('')) == []


class TestReadIgnoreFile:
    def test_returns_empty_list_when_file_missing(self, tmp_path: pathlib.Path) -> None:
        assert _read_ignore_file(str(tmp_path / 'nope')) == []

    def test_reads_and_parses_existing_file(self, tmp_path: pathlib.Path) -> None:
        f = tmp_path / 'ignore'
        f.write_text('a\n# comment\nb\n')

        assert _read_ignore_file(str(f)) == ['a', 'b']


class TestGitignoreExcludeRules:
    def test_empty_when_no_files_present(self, tmp_path: pathlib.Path) -> None:
        assert gitignore_exclude_rules(str(tmp_path)) == []

    def test_plain_lines_get_deny_prefix(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / '.gitignore').write_text('node_modules/\n*.pyc\n')

        assert gitignore_exclude_rules(str(tmp_path)) == [
            '- node_modules/',
            '- *.pyc',
        ]

    def test_negation_translated_and_bucketed_first(
        self, tmp_path: pathlib.Path
    ) -> None:
        (tmp_path / '.gitignore').write_text('build/*\n!build/keep.txt\n')

        assert gitignore_exclude_rules(str(tmp_path)) == [
            '+ build/keep.txt',
            '- build/*',
        ]

    def test_combines_git_info_exclude_and_gitignore(
        self, tmp_path: pathlib.Path
    ) -> None:
        git_dir = tmp_path / '.git' / 'info'
        git_dir.mkdir(parents=True)
        (git_dir / 'exclude').write_text('*.swp\n!important.swp\n')
        (tmp_path / '.gitignore').write_text('dist/\n!dist/keep/\n')

        rules = gitignore_exclude_rules(str(tmp_path))

        assert rules == [
            '+ important.swp',
            '+ dist/keep/',
            '- *.swp',
            '- dist/',
        ]

    def test_bare_lone_bang_gets_deny_prefix(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / '.gitignore').write_text('!\nfoo\n')

        assert gitignore_exclude_rules(str(tmp_path)) == ['- !', '- foo']
