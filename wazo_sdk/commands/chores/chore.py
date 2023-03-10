# Copyright 2021-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


class Chore:
    name = 'undefined'

    @classmethod
    def print_expectations(cls) -> None:
        print('Undefined expectations')

    @classmethod
    def is_applicable(cls, repo_path: str) -> bool:
        return True

    @classmethod
    def is_dirty(cls, repo_path: str) -> bool:
        return True

    @classmethod
    def print_dirty_details(cls, repo_path: str, repo_name: str) -> None:
        print(repo_name)
