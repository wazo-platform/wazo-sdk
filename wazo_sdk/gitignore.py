# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import annotations

import os
from typing import TextIO


def _read_ignore_lines(stream: TextIO) -> list[str]:
    return [
        stripped
        for line in stream
        if (stripped := line.strip()) and not stripped.startswith(('#', ';'))
    ]


def _read_ignore_file(path: str) -> list[str]:
    try:
        with open(path) as f:
            return _read_ignore_lines(f)
    except OSError:
        return []


def gitignore_exclude_rules(repo_path: str) -> list[str]:
    "translate gitignore patterns into rsync exclusion rules"
    lines = _read_ignore_file(
        os.path.join(repo_path, '.git', 'info', 'exclude')
    ) + _read_ignore_file(os.path.join(repo_path, '.gitignore'))

    negations = [
        f'+ {line[1:]}' for line in lines if line.startswith('!') and line != '!'
    ]
    plain = [line for line in lines if not (line.startswith('!') and line != '!')]
    return negations + plain
