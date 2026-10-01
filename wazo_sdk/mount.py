# Copyright 2018-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import annotations

import logging
import os
import shlex
import signal
import subprocess
import tempfile
import time
from collections.abc import Generator
from logging import Logger
from typing import TYPE_CHECKING, Any

import psutil
import sh
from jinja2 import Template

from wazo_sdk.config import Config
from wazo_sdk.state import State

if TYPE_CHECKING:
    from wazo_sdk.config import Project
    from wazo_sdk.state import MountData


_logger = logging.getLogger(__name__)


class SyncError(Exception):
    pass


def read_pidfile(path: str) -> int | None:
    try:
        with open(path) as f:
            return int(f.read().strip())
    except (OSError, ValueError) as ex:
        _logger.debug('error reading pidfile %s: %s', path, ex)
        return None


def is_lsyncd_pid(pid: int) -> bool:
    if pid not in psutil.pids():
        return False
    try:
        with open(os.path.join('/proc', str(pid), 'status')) as f:
            _, cmd = f.readline().strip().rsplit('\t', 1)
            return cmd == 'lsyncd'
    except OSError as e:
        _logger.warning('could not read /proc/%s/status: %s', pid, e)
        return False


REPO_PREFIX = ['', 'wazo-', 'xivo-']
LSYNCD_STOP_TIMEOUT = 5.0
LSYNCD_STOP_POLL_INTERVAL = 0.1
LSYNC_CONFIG_TEMPLATE = Template(
    '''\
sync {
    default.rsync,
    delay = 1,
    source = "{{ source }}",
    target = "{{ host }}:{{ destination }}",
    exclude = {'.git', '.tox', 'node_modules', '__pycache__', '*.pyc'},
    rsync = {
        xattrs = true,
        archive = true,
        perms = true
    }
}
'''
)

RSYNC_OPTIONS = [
    '--xattrs',
    '--archive',
    '--perms',
    '--delete',
    '--exclude=.git',
    '--exclude=.tox',
    '--exclude=node_modules',
    '--exclude=__pycache__',
    '--exclude=*.pyc',
]


def _list_processes() -> Generator[tuple[int, str], None, None]:
    for pid in psutil.pids():
        try:
            with open(
                os.path.join(
                    '/proc',
                    str(pid),
                    'cmdline',
                ),
            ) as f:
                yield pid, f.read()[:-1]
        except OSError:
            # Process already completed
            pass


class Mounter:
    def __init__(self, logger: Logger, config: Config, state: State) -> None:
        self.logger = logger
        self._config = config
        self._hostname: str = config.hostname  # type: ignore
        self._local_dir: str = config.local_source
        self._remote_dir: str = config.remote_source  # type: ignore
        self._state = state

    def list_(self) -> Generator[tuple[str, bool, str | None], None, None]:
        mounts = self._state.get_mounts(self._hostname)
        for mount in mounts.values():
            if not mount:
                continue
            yield (
                mount['project'],
                self._is_sync_running(mount),
                mount.get('local_path'),
            )

    def _is_sync_running(self, mount: MountData) -> bool:
        if self._config.rsync_only:
            return True

        pid_filename = mount['lsync_pidfile']
        if not pid_filename:
            return False

        pid = read_pidfile(pid_filename)
        if pid is None:
            return False

        return is_lsyncd_pid(pid)

    def _is_mounted(self, repo_name: str) -> bool:
        return self._state.is_mounted(self._hostname, repo_name)

    def _is_mounted_and_running(self, repo_name: str) -> bool:
        mount = self._state.get_mount(self._hostname, repo_name)
        if not mount:
            return False
        return self._is_sync_running(mount)

    def mount(self, repo_name: str, local_path: str | None = None) -> None:
        if not self._hostname:
            raise Exception('The remote hostname is required to mount directories')

        local_dir = self._resolve_local_dir(repo_name, local_path)
        real_repo_name = self._config.get_project_name(repo_name)

        # Skip sync if lsync is already running (rsync-only always re-syncs)
        if not self._config.rsync_only and self._is_mounted_and_running(real_repo_name):
            mounted_dir = self._mounted_local_dir(real_repo_name)
            if mounted_dir == local_dir:
                self.logger.debug('%s is already mounted', real_repo_name)
            else:
                if mounted_dir:
                    self.logger.info(
                        '%s is mounted from %s, switching to %s',
                        real_repo_name,
                        mounted_dir,
                        local_dir,
                    )
                else:
                    # state predates local path recording: the synced checkout
                    # is unknown, so re-sync rather than keep the wrong one
                    self.logger.info(
                        '%s is mounted from an unrecorded checkout, re-syncing from %s',
                        real_repo_name,
                        local_dir,
                    )
                self._stop_sync(real_repo_name)
                self._start_sync(local_dir, real_repo_name)
        else:
            self._start_sync(local_dir, real_repo_name)

        repo_config = self._config.get_project(real_repo_name)
        self._apply_mount(real_repo_name, repo_config)

    def _resolve_local_dir(self, repo_name: str, local_path: str | None) -> str:
        if local_path:
            local_dir = os.path.abspath(os.path.expanduser(local_path))
            if not os.path.isdir(local_dir):
                raise Exception(f'No such directory {local_dir}')
            return local_dir

        if not self._local_dir:
            raise Exception(
                'The local source directory is required to mount directories'
            )
        return os.path.join(self._local_dir, self._find_local_repo_name(repo_name))

    def _mounted_local_dir(self, repo_name: str) -> str | None:
        mount = self._state.get_mount(self._hostname, repo_name)
        if not mount:
            return None
        return mount.get('local_path')

    def umount(self, repo_name: str) -> None:
        if not self._local_dir:
            raise Exception(
                'The local source directory is required to mount directories'
            )

        real_repo_name = self._config.get_project_name(repo_name)

        repo_config = self._config.get_project(real_repo_name)
        self._unapply_mount(real_repo_name, repo_config)

        if not self._is_mounted(real_repo_name):
            self.logger.debug('%s is not mounted', real_repo_name)
        else:
            self._stop_sync(real_repo_name)
            self._state.remove_mount(self._hostname, real_repo_name)

    def _apply_mount(self, repo_name: str, project: Project) -> None:
        wazo = sh.ssh.bake(self._hostname)
        if project.python3:
            self._mount_python3(wazo, repo_name)
        if project.bind:
            self._bind_files(wazo, repo_name, project.bind)

    def _unapply_mount(self, repo_name: str, project: Project) -> None:
        wazo = sh.ssh.bake(self._hostname)
        if project.python3:
            self._umount_python3(wazo, repo_name)
        if project.bind:
            self._remove_bind_files(wazo, repo_name, project.bind)
        clean = project.clean
        if clean:
            self._clean_files(wazo, clean)

    def _bind_files(
        self, ssh: sh.Command, repo_name: str, binds: dict[str, str]
    ) -> None:
        mount_output = ssh('mount').strip().split('\n')
        mounted: list[str] = []
        for line in mount_output:
            cols = line.split(' ')
            mounted.append(cols[2])

        self.logger.debug('mounted: %s', mounted)

        for source, dest in binds.items():
            if dest in mounted:
                self.logger.debug('%s is already mounted...', dest)
                continue
            src_path = os.path.join(self._remote_dir, repo_name, source)
            self._wait_for_file(ssh, src_path)
            self._ensure_dest_exists(ssh, src_path, dest)
            cmd = f'mount --bind {shlex.quote(src_path)} {shlex.quote(dest)}'
            self.logger.debug(ssh(cmd))

    def _clean_files(self, ssh: sh.Command, files: list[str]) -> None:
        ssh(f'rm -rf {" ".join(shlex.quote(f) for f in files)}')

    def _remove_bind_files(
        self, ssh: sh.Command, repo_name: str, binds: dict[str, str]
    ) -> None:
        mount_output = ssh('mount').strip().split('\n')
        mounted = []
        for line in mount_output:
            cols = line.split(' ')
            mounted.append(cols[2])

        self.logger.debug('mounted: %s', mounted)

        for source, dest in binds.items():
            if dest not in mounted:
                continue

            cmd = f'umount {shlex.quote(dest)}'
            self.logger.debug(ssh(cmd))

    def _mount_python3(self, ssh: sh.Command, repo_name: str) -> None:
        setup_path = os.path.join(self._remote_dir, repo_name, 'setup.py')
        self._wait_for_file(ssh, setup_path)

        repo_dir = os.path.join(self._remote_dir, repo_name)
        # -N flag ensures the dependencies are not installed/updated,
        # in order to retain consistency of debian packaging
        cmd = f'cd {shlex.quote(repo_dir)} && python3 setup.py develop -N'
        self.logger.debug(ssh(cmd))

    def _umount_python3(self, ssh: sh.Command, repo_name: str) -> None:
        repo_dir = os.path.join(self._remote_dir, repo_name)
        cmd = f'cd {shlex.quote(repo_dir)} && python3 setup.py develop --uninstall'
        self.logger.debug(ssh(cmd))

    def _ensure_dest_exists(self, ssh: sh.Command, src_path: str, dest: str) -> None:
        q_dest = shlex.quote(dest)
        q_src = shlex.quote(src_path)
        ssh(
            f'if [ ! -e {q_dest} ]; then '
            f'if [ -d {q_src} ]; then mkdir -p {q_dest}; '
            f'else mkdir -p "$(dirname {q_dest})" && touch {q_dest}; fi; fi'
        )

    def _wait_for_file(self, ssh: sh.Command, filename: str) -> None:
        ssh(f'while [ ! -e {shlex.quote(filename)} ]; do sleep 0.2; done')

    def _start_sync(self, local_path: str, real_repo_name: str) -> None:
        remote_path = os.path.join(self._remote_dir, real_repo_name)
        config_filename: str | None = None
        pid_filename: str | None = None
        communicate_kwargs: dict[str, Any] = {}

        if self._config.rsync_only:
            sync_command = [
                'rsync',
                *RSYNC_OPTIONS,
                f'{local_path}/',
                f'{self._hostname}:{remote_path}/',
            ]
        else:
            config = LSYNC_CONFIG_TEMPLATE.render(
                source=local_path, host=self._hostname, destination=remote_path
            )

            with tempfile.NamedTemporaryFile(
                mode='w', dir=self._config.cache_dir, delete=False
            ) as f:
                config_filename = f.name
                f.write(config)

            pid_filename = f'{config_filename}.pid'
            sync_command = ['lsyncd', config_filename, '--pidfile', pid_filename]
            communicate_kwargs = {'timeout': 1}

        self.logger.debug('%s', ' '.join(sync_command))
        proc = subprocess.Popen(sync_command, stderr=subprocess.PIPE)
        success = False
        try:
            _, errs = proc.communicate(**communicate_kwargs)
            if proc.returncode != 0:
                stderr_msg = errs.decode(errors='replace').strip() if errs else ''
                raise SyncError(
                    f'{sync_command[0]} failed (exit {proc.returncode})'
                    + (f': {stderr_msg}' if stderr_msg else '')
                )
            success = True
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            raise SyncError(
                f'{sync_command[0]} did not daemonize within timeout'
            ) from None
        finally:
            if not success:
                self._cleanup_sync_files(config_filename, pid_filename)

        self._state.add_mount(
            self._hostname, real_repo_name, config_filename, pid_filename, local_path
        )

    def _cleanup_sync_files(
        self, config_filename: str | None, pid_filename: str | None
    ) -> None:
        for path in (config_filename, pid_filename):
            if path:
                try:
                    os.unlink(path)
                except OSError:
                    pass

    def _stop_sync(self, repo_name: str) -> None:
        mount = self._state.get_mount(self._hostname, repo_name)
        if not mount:
            self.logger.error('failed to find a matching mount to stop')
            return

        if not self._config.rsync_only:
            pid_filename = mount['lsync_pidfile']
            pid = read_pidfile(pid_filename) if pid_filename else None

            if pid:
                self._terminate_lsyncd(pid)

            for path in (pid_filename, mount['lsync_config']):
                if path:
                    try:
                        os.unlink(path)
                    except OSError:
                        pass

    def _terminate_lsyncd(self, pid: int) -> None:
        # a stale pidfile may point at a recycled pid belonging to something else
        if not is_lsyncd_pid(pid):
            self.logger.debug('pid %s is not lsyncd, leaving it alone', pid)
            return

        if not self._signal_lsyncd(pid, signal.SIGTERM):
            return

        if self._wait_for_lsyncd_exit(pid, LSYNCD_STOP_TIMEOUT):
            return

        self.logger.warning(
            'lsyncd %s did not stop after %ss, killing it', pid, LSYNCD_STOP_TIMEOUT
        )
        if not self._signal_lsyncd(pid, signal.SIGKILL):
            return

        if not self._wait_for_lsyncd_exit(pid, LSYNCD_STOP_TIMEOUT):
            self.logger.error('lsyncd %s is still running after SIGKILL', pid)

    def _signal_lsyncd(self, pid: int, sig: int) -> bool:
        try:
            os.kill(pid, sig)
        except ProcessLookupError:
            return False
        except OSError as ex:
            self.logger.error('failed to signal %s: %s', pid, ex)
            return False
        return True

    def _wait_for_lsyncd_exit(self, pid: int, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while is_lsyncd_pid(pid):
            if time.monotonic() >= deadline:
                return False
            time.sleep(LSYNCD_STOP_POLL_INTERVAL)
        return True

    def _find_local_repo_name(self, repo_name: str) -> str:
        for prefix in REPO_PREFIX:
            basename = f'{prefix}{repo_name}'
            path = os.path.join(self._local_dir, basename)
            if os.path.exists(path):
                return basename

        raise Exception(f'No such repo {repo_name}')
