#!/usr/bin/env python3
# Copyright 2018-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from setuptools import find_packages, setup

NAME = 'wdk'
setup(
    name=NAME,
    version='0.1',
    author='Wazo Authors',
    author_email='dev@wazo.community',
    url='http://wazo.community',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            f'{NAME}=wazo_sdk.main:main',
        ],
        'wazo_sdk.commands': [
            'init = wazo_sdk.commands.init:Init',
            'info = wazo_sdk.commands.info:Info',
            'chores = wazo_sdk.commands.chores_:ChoreList',
            'mount = wazo_sdk.commands.mount:Mount',
            'umount = wazo_sdk.commands.mount:Umount',
            'restart = wazo_sdk.commands.restart:Restart',
            'repo_clone = wazo_sdk.commands.repos.clone:RepoClone',
            'repo_rm_orphan = wazo_sdk.commands.repos.rm_orphan:RemoveOrphanRepo',
            'tailf = wazo_sdk.commands.tailf:Tailf',
        ],
    },
)
