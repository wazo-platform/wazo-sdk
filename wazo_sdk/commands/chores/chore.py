# Copyright 2021-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


class Chore:
    name = 'undefined'

    @classmethod
    def print_expectations(cls):
        print('Undefined expectations')

    @classmethod
    def is_applicable(cls, repo_path):
        return True

    @classmethod
    def is_dirty(cls, repo_path):
        return True

    @classmethod
    def print_dirty_details(cls, repo_path, repo_name):
        print(repo_name)
