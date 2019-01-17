#!/usr/bin/env python3
# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from setuptools import setup
from setuptools import find_packages


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
            '{}=wazo_sdk.main:main'.format(NAME),
        ],
        'wazo_sdk.commands': [
            'info = wazo_sdk.commands.info:Info',
            'mount = wazo_sdk.commands.mount:Mount',
            'umount = wazo_sdk.commands.mount:Umount',
            'restart = wazo_sdk.commands.restart:Restart',
            'repo_clone = wazo_sdk.commands.repo_clone:RepoClone',
        ],
    },
)
