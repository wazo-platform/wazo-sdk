# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import annotations

import pathlib
import subprocess
from unittest.mock import MagicMock, mock_open, patch

import pytest

from wazo_sdk.mount import Mounter, SyncError, is_lsyncd_pid


@pytest.fixture
def config() -> MagicMock:
    config = MagicMock()
    config.hostname = 'test-host'
    config.local_source = '/local/src'
    config.remote_source = '/usr/src/wazo'
    return config


@pytest.fixture
def state() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mounter(config: MagicMock, state: MagicMock) -> Mounter:
    logger = MagicMock()
    return Mounter(logger, config, state)


@pytest.fixture
def ssh() -> MagicMock:
    return MagicMock()


class TestEnsureDestExists:
    def test_creates_directory_when_source_is_directory(
        self, mounter: Mounter, ssh: MagicMock
    ) -> None:
        src = '/usr/src/wazo/repo/dialplan'
        dest = '/usr/share/asterisk/dialplan'
        mounter._ensure_dest_exists(ssh, src, dest)

        ssh.assert_called_once()
        cmd = ssh.call_args[0][0]
        assert f'mkdir -p {dest}' in cmd
        assert f'! -e {dest}' in cmd

    def test_creates_file_when_source_is_file(
        self, mounter: Mounter, ssh: MagicMock
    ) -> None:
        src = '/usr/src/wazo/repo/etc/config.yml'
        dest = '/etc/wazo/config.yml'
        mounter._ensure_dest_exists(ssh, src, dest)

        ssh.assert_called_once()
        cmd = ssh.call_args[0][0]
        assert f'! -e {dest}' in cmd
        assert f'touch {dest}' in cmd
        assert 'mkdir -p' in cmd

    def test_guarded_by_dest_existence_check(
        self, mounter: Mounter, ssh: MagicMock
    ) -> None:
        dest = '/etc/wazo/config.yml'
        mounter._ensure_dest_exists(ssh, '/usr/src/wazo/repo/etc/config.yml', dest)

        cmd = ssh.call_args[0][0]
        assert cmd.startswith(f'if [ ! -e {dest} ]')

    def test_uses_single_ssh_call(self, mounter: Mounter, ssh: MagicMock) -> None:
        mounter._ensure_dest_exists(ssh, '/usr/src/wazo/repo/file', '/etc/file')
        ssh.assert_called_once()


class TestBindFiles:
    def test_skips_already_mounted(self, mounter: Mounter, ssh: MagicMock) -> None:
        ssh.return_value = (
            '/dev/sda1 on / type ext4\n' '/src on /etc/config.yml type none'
        )
        binds = {'etc/config.yml': '/etc/config.yml'}

        mounter._bind_files(ssh, 'my-repo', binds)

        assert ssh.call_count == 1

    def test_creates_placeholder_before_mounting(
        self, mounter: Mounter, ssh: MagicMock
    ) -> None:
        ssh.return_value = '/dev/sda1 on / type ext4'
        binds = {'etc/config.yml': '/etc/wazo/config.yml'}

        mounter._bind_files(ssh, 'my-repo', binds)

        cmds = [c[0][0] for c in ssh.call_args_list]
        ensure_cmd = next(c for c in cmds if c.startswith('if [ ! -e'))
        assert 'mkdir -p' in ensure_cmd
        assert 'touch /etc/wazo/config.yml' in ensure_cmd
        assert any('mount --bind' in c for c in cmds)

    def test_ensure_dest_called_after_wait_for_file(
        self, mounter: Mounter, ssh: MagicMock
    ) -> None:
        ssh.return_value = '/dev/sda1 on / type ext4'
        binds = {'etc/config.yml': '/etc/wazo/config.yml'}

        mounter._bind_files(ssh, 'my-repo', binds)

        calls = [c[0][0] for c in ssh.call_args_list]
        wait_idx = next(i for i, c in enumerate(calls) if 'while' in c)
        ensure_idx = next(i for i, c in enumerate(calls) if c.startswith('if [ ! -e'))
        mount_idx = next(i for i, c in enumerate(calls) if 'mount --bind' in c)
        assert wait_idx < ensure_idx < mount_idx

    def test_mounts_multiple_binds(self, mounter: Mounter, ssh: MagicMock) -> None:
        ssh.return_value = '/dev/sda1 on / type ext4'
        binds = {
            'etc/config.yml': '/etc/wazo/config.yml',
            'templates': '/var/lib/wazo/templates',
        }

        mounter._bind_files(ssh, 'my-repo', binds)

        mount_calls = [c for c in ssh.call_args_list if 'mount --bind' in str(c)]
        assert len(mount_calls) == 2

    def test_constructs_correct_source_path(
        self, mounter: Mounter, ssh: MagicMock
    ) -> None:
        ssh.return_value = '/dev/sda1 on / type ext4'
        binds = {'etc/conf.d/50-new.yml': '/etc/svc/conf.d/50-new.yml'}

        mounter._bind_files(ssh, 'wazo-auth', binds)

        mount_call = next(
            c[0][0] for c in ssh.call_args_list if 'mount --bind' in c[0][0]
        )
        expected_src = '/usr/src/wazo/wazo-auth/etc/conf.d/50-new.yml'
        assert expected_src in mount_call

    def test_skips_some_already_mounted_mounts_others(
        self, mounter: Mounter, ssh: MagicMock
    ) -> None:
        ssh.return_value = (
            '/dev/sda1 on / type ext4\n' '/src on /etc/existing.yml type none'
        )
        binds = {
            'etc/existing.yml': '/etc/existing.yml',
            'etc/new.yml': '/etc/new.yml',
        }

        mounter._bind_files(ssh, 'my-repo', binds)

        mount_calls = [c[0][0] for c in ssh.call_args_list if 'mount --bind' in c[0][0]]
        assert len(mount_calls) == 1
        assert '/etc/new.yml' in mount_calls[0]

    def test_empty_binds(self, mounter: Mounter, ssh: MagicMock) -> None:
        ssh.return_value = '/dev/sda1 on / type ext4'

        mounter._bind_files(ssh, 'my-repo', {})

        assert not any('mount --bind' in c[0][0] for c in ssh.call_args_list)


class TestStartSync:
    def test_rsync_command_excludes_are_separate_args(
        self, mounter: Mounter, config: MagicMock
    ) -> None:
        # subprocess.Popen runs argv directly (no shell), so a single
        # "--exclude={'a','b'}" arg is passed to rsync literally and
        # excludes nothing; each pattern must be its own --exclude arg.
        config.rsync_only = True
        proc = MagicMock()
        proc.communicate.return_value = (None, None)
        proc.returncode = 0

        with patch('subprocess.Popen', return_value=proc) as popen:
            mounter._start_sync('my-repo', 'my-repo')

        command = popen.call_args[0][0]
        assert '--exclude=.git' in command
        assert '--exclude=.tox' in command
        assert '--exclude=node_modules' in command
        assert not any('{' in arg for arg in command)

    def test_rsync_failure_raises(
        self, mounter: Mounter, config: MagicMock, state: MagicMock
    ) -> None:
        config.rsync_only = True
        proc = MagicMock()
        proc.communicate.return_value = (None, b'error: connection refused')
        proc.returncode = 1

        with patch('subprocess.Popen', return_value=proc):
            with pytest.raises(SyncError, match='rsync'):
                mounter._start_sync('my-repo', 'my-repo')

        state.add_mount.assert_not_called()

    def test_rsync_success_records_state(
        self, mounter: Mounter, config: MagicMock, state: MagicMock
    ) -> None:
        config.rsync_only = True
        proc = MagicMock()
        proc.communicate.return_value = (None, None)
        proc.returncode = 0

        with patch('subprocess.Popen', return_value=proc):
            mounter._start_sync('my-repo', 'my-repo')

        state.add_mount.assert_called_once()

    def test_lsyncd_failure_raises(
        self,
        mounter: Mounter,
        config: MagicMock,
        state: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        config.rsync_only = False
        config.cache_dir = str(tmp_path)
        proc = MagicMock()
        proc.communicate.return_value = (None, b'lsyncd: bad config')
        proc.returncode = 1

        with patch('subprocess.Popen', return_value=proc):
            with pytest.raises(SyncError, match='lsyncd'):
                mounter._start_sync('my-repo', 'my-repo')

        state.add_mount.assert_not_called()

    def test_lsyncd_timeout_kills_process_and_raises(
        self,
        mounter: Mounter,
        config: MagicMock,
        state: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        config.rsync_only = False
        config.cache_dir = str(tmp_path)
        proc = MagicMock()
        proc.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd='lsyncd', timeout=1),
            (None, None),
        ]

        with patch('subprocess.Popen', return_value=proc):
            with pytest.raises(SyncError, match='lsyncd'):
                mounter._start_sync('my-repo', 'my-repo')

        proc.kill.assert_called_once()
        state.add_mount.assert_not_called()

    def test_lsyncd_timeout_reaps_process(
        self,
        mounter: Mounter,
        config: MagicMock,
        state: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        config.rsync_only = False
        config.cache_dir = str(tmp_path)
        proc = MagicMock()
        proc.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd='lsyncd', timeout=1),
            (None, None),
        ]

        with patch('subprocess.Popen', return_value=proc):
            with pytest.raises(SyncError):
                mounter._start_sync('my-repo', 'my-repo')

        assert proc.communicate.call_count == 2

    def test_lsyncd_timeout_does_not_chain_traceback(
        self,
        mounter: Mounter,
        config: MagicMock,
        state: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        config.rsync_only = False
        config.cache_dir = str(tmp_path)
        proc = MagicMock()
        proc.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd='lsyncd', timeout=1),
            (None, None),
        ]

        with patch('subprocess.Popen', return_value=proc):
            try:
                mounter._start_sync('my-repo', 'my-repo')
            except SyncError as exc:
                assert exc.__suppress_context__ is True
            else:
                pytest.fail('SyncError was not raised')

    def test_lsyncd_failure_unlinks_config_file(
        self,
        mounter: Mounter,
        config: MagicMock,
        state: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        config.rsync_only = False
        config.cache_dir = str(tmp_path)
        proc = MagicMock()
        proc.communicate.return_value = (None, b'lsyncd: bad config')
        proc.returncode = 1

        with patch('subprocess.Popen', return_value=proc):
            with pytest.raises(SyncError, match='lsyncd'):
                mounter._start_sync('my-repo', 'my-repo')

        assert list(tmp_path.iterdir()) == []

    def test_lsyncd_timeout_unlinks_config_file(
        self,
        mounter: Mounter,
        config: MagicMock,
        state: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        config.rsync_only = False
        config.cache_dir = str(tmp_path)
        proc = MagicMock()
        proc.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd='lsyncd', timeout=1),
            (None, None),
        ]

        with patch('subprocess.Popen', return_value=proc):
            with pytest.raises(SyncError):
                mounter._start_sync('my-repo', 'my-repo')

        assert list(tmp_path.iterdir()) == []


class TestIsLsyncdPid:
    def test_returns_false_when_pid_not_running(self) -> None:
        with patch('wazo_sdk.mount.psutil.pids', return_value=[]):
            assert is_lsyncd_pid(12345) is False

    def test_returns_true_when_pid_is_lsyncd(self) -> None:
        with (
            patch('wazo_sdk.mount.psutil.pids', return_value=[12345]),
            patch('builtins.open', mock_open(read_data='Name\tlsyncd\n')),
        ):
            assert is_lsyncd_pid(12345) is True

    def test_returns_false_when_pid_is_not_lsyncd(self) -> None:
        with (
            patch('wazo_sdk.mount.psutil.pids', return_value=[12345]),
            patch('builtins.open', mock_open(read_data='Name\tpython3\n')),
        ):
            assert is_lsyncd_pid(12345) is False

    def test_returns_false_and_logs_on_oserror(self) -> None:
        with (
            patch('wazo_sdk.mount.psutil.pids', return_value=[12345]),
            patch('builtins.open', side_effect=OSError('permission denied')),
            patch('wazo_sdk.mount._logger') as mock_logger,
        ):
            result = is_lsyncd_pid(12345)

        assert result is False
        mock_logger.warning.assert_called_once()


class TestStopSync:
    def test_deletes_pidfile_on_stop(
        self,
        mounter: Mounter,
        config: MagicMock,
        state: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        pid_file = tmp_path / 'lsyncd.pid'
        pid_file.write_text('99999')
        config.rsync_only = False
        state.get_mount.return_value = {
            'project': 'my-repo',
            'lsync_config': str(tmp_path / 'config'),
            'lsync_pidfile': str(pid_file),
        }

        with patch('os.kill'):
            mounter._stop_sync('my-repo')

        assert not pid_file.exists()

    def test_deletes_pidfile_even_if_kill_fails(
        self,
        mounter: Mounter,
        config: MagicMock,
        state: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        pid_file = tmp_path / 'lsyncd.pid'
        pid_file.write_text('99999')
        config.rsync_only = False
        state.get_mount.return_value = {
            'project': 'my-repo',
            'lsync_config': str(tmp_path / 'config'),
            'lsync_pidfile': str(pid_file),
        }

        with patch('os.kill', side_effect=OSError('no such process')):
            mounter._stop_sync('my-repo')

        assert not pid_file.exists()

    def test_rsync_only_removes_state(
        self, mounter: Mounter, config: MagicMock, state: MagicMock
    ) -> None:
        config.rsync_only = True
        state.get_mount.return_value = {
            'project': 'my-repo',
            'lsync_config': None,
            'lsync_pidfile': None,
        }

        mounter._stop_sync('my-repo')

        state.remove_mount.assert_called_once_with('test-host', 'my-repo')

    def test_rsync_only_noop_when_not_mounted(
        self, mounter: Mounter, config: MagicMock, state: MagicMock
    ) -> None:
        config.rsync_only = True
        state.get_mount.return_value = None

        mounter._stop_sync('my-repo')

        state.remove_mount.assert_not_called()

    def test_removes_state_when_pidfile_is_none(
        self, mounter: Mounter, config: MagicMock, state: MagicMock
    ) -> None:
        config.rsync_only = False
        state.get_mount.return_value = {
            'project': 'my-repo',
            'lsync_config': None,
            'lsync_pidfile': None,
        }

        mounter._stop_sync('my-repo')

        state.remove_mount.assert_called_once_with('test-host', 'my-repo')

    def test_removes_state_when_pidfile_content_is_invalid(
        self,
        mounter: Mounter,
        config: MagicMock,
        state: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        pid_file = tmp_path / 'lsyncd.pid'
        pid_file.write_text('not-a-pid')
        config.rsync_only = False
        state.get_mount.return_value = {
            'project': 'my-repo',
            'lsync_config': str(tmp_path / 'config'),
            'lsync_pidfile': str(pid_file),
        }

        mounter._stop_sync('my-repo')

        state.remove_mount.assert_called_once_with('test-host', 'my-repo')

    def test_deletes_lsync_config_on_stop(
        self,
        mounter: Mounter,
        config: MagicMock,
        state: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        pid_file = tmp_path / 'lsyncd.pid'
        pid_file.write_text('99999')
        config_file = tmp_path / 'config'
        config_file.write_text('sync {}')
        config.rsync_only = False
        state.get_mount.return_value = {
            'project': 'my-repo',
            'lsync_config': str(config_file),
            'lsync_pidfile': str(pid_file),
        }

        with patch('os.kill'):
            mounter._stop_sync('my-repo')

        assert not config_file.exists()


class TestBindFilesErrorPaths:
    def test_wait_for_file_failure_skips_ensure_and_mount(
        self, mounter: Mounter, ssh: MagicMock
    ) -> None:
        call_count = 0

        def side_effect(cmd: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return '/dev/sda1 on / type ext4'
            if 'while' in cmd:
                raise Exception('SSH timeout')
            return ''

        ssh.side_effect = side_effect
        binds = {'etc/config.yml': '/etc/wazo/config.yml'}

        with pytest.raises(Exception, match='SSH timeout'):
            mounter._bind_files(ssh, 'my-repo', binds)

        cmds = [c[0][0] for c in ssh.call_args_list]
        assert not any('if [ ! -e' in c for c in cmds)
        assert not any('mount --bind' in c for c in cmds)

    def test_ensure_dest_failure_skips_mount(
        self, mounter: Mounter, ssh: MagicMock
    ) -> None:
        call_count = 0

        def side_effect(cmd: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return '/dev/sda1 on / type ext4'
            if cmd.startswith('if [ ! -e'):
                raise Exception('SSH failed')
            return ''

        ssh.side_effect = side_effect
        binds = {'etc/config.yml': '/etc/wazo/config.yml'}

        with pytest.raises(Exception, match='SSH failed'):
            mounter._bind_files(ssh, 'my-repo', binds)

        cmds = [c[0][0] for c in ssh.call_args_list]
        assert not any('mount --bind' in c for c in cmds)
