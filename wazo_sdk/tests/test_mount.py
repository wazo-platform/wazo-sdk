# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import annotations

import json
import pathlib
import signal
import subprocess
from unittest.mock import MagicMock, call, mock_open, patch

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


class TestPythonEditableInstall:
    def test_mount_uses_pip_editable_install(
        self, mounter: Mounter, ssh: MagicMock
    ) -> None:
        mounter._mount_python3(ssh, 'my-repo')

        cmd = ssh.call_args[0][0]
        assert 'pip install --break-system-packages --no-deps -e' in cmd
        assert '/usr/src/wazo/my-repo' in cmd
        assert 'setup.py' not in cmd

    def test_umount_uninstalls_package_found_by_project_location(
        self, mounter: Mounter, ssh: MagicMock
    ) -> None:
        packages = [
            {'name': 'other', 'editable_project_location': '/usr/src/wazo/other'},
            {'name': 'my_pkg', 'editable_project_location': '/usr/src/wazo/my-repo'},
        ]
        ssh.return_value = json.dumps(packages)

        mounter._umount_python3(ssh, 'my-repo')

        cmds = [c[0][0] for c in ssh.call_args_list]
        assert 'pip list' in cmds[0] and '--format json' in cmds[0]
        assert 'pip uninstall --break-system-packages -y my_pkg' in cmds[1]
        assert len(cmds) == 2

    def test_umount_does_nothing_when_not_installed(
        self, mounter: Mounter, ssh: MagicMock
    ) -> None:
        ssh.return_value = json.dumps(
            [{'name': 'other', 'editable_project_location': '/usr/src/wazo/other'}]
        )

        mounter._umount_python3(ssh, 'my-repo')

        assert ssh.call_count == 1


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
            mounter._start_sync('/local/src/my-repo', 'my-repo')

        command = popen.call_args[0][0]
        assert '--exclude=.git' in command
        assert '--exclude=.tox' in command
        assert '--exclude=node_modules' in command
        assert '--exclude=__pycache__' in command
        assert '--exclude=*.pyc' in command
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
                mounter._start_sync('/local/src/my-repo', 'my-repo')

        state.add_mount.assert_not_called()

    def test_rsync_success_records_state(
        self, mounter: Mounter, config: MagicMock, state: MagicMock
    ) -> None:
        config.rsync_only = True
        proc = MagicMock()
        proc.communicate.return_value = (None, None)
        proc.returncode = 0

        with patch('subprocess.Popen', return_value=proc):
            mounter._start_sync('/local/src/my-repo', 'my-repo')

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
                mounter._start_sync('/local/src/my-repo', 'my-repo')

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
                mounter._start_sync('/local/src/my-repo', 'my-repo')

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
                mounter._start_sync('/local/src/my-repo', 'my-repo')

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
                mounter._start_sync('/local/src/my-repo', 'my-repo')
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
                mounter._start_sync('/local/src/my-repo', 'my-repo')

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
                mounter._start_sync('/local/src/my-repo', 'my-repo')

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

    def test_leaves_state_alone(
        self, mounter: Mounter, config: MagicMock, state: MagicMock
    ) -> None:
        # forgetting a mount belongs to umount, not to stopping its sync
        config.rsync_only = True
        state.get_mount.return_value = {
            'project': 'my-repo',
            'lsync_config': None,
            'lsync_pidfile': None,
        }

        mounter._stop_sync('my-repo')

        state.remove_mount.assert_not_called()

    def test_noop_when_not_mounted(
        self, mounter: Mounter, config: MagicMock, state: MagicMock
    ) -> None:
        config.rsync_only = True
        state.get_mount.return_value = None

        mounter._stop_sync('my-repo')

        state.remove_mount.assert_not_called()

    def test_tolerates_a_missing_pidfile(
        self, mounter: Mounter, config: MagicMock, state: MagicMock
    ) -> None:
        config.rsync_only = False
        state.get_mount.return_value = {
            'project': 'my-repo',
            'lsync_config': None,
            'lsync_pidfile': None,
        }

        with patch('os.kill') as kill:
            mounter._stop_sync('my-repo')

        kill.assert_not_called()

    def test_deletes_pidfile_when_its_content_is_invalid(
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

        with patch('os.kill') as kill:
            mounter._stop_sync('my-repo')

        kill.assert_not_called()
        assert not pid_file.exists()

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


class TestResolveLocalDir:
    def test_override_is_absolute_and_expanded(
        self, mounter: Mounter, tmp_path: pathlib.Path
    ) -> None:
        checkout = tmp_path / 'worktree-ITEM-123'
        checkout.mkdir()

        resolved = mounter._resolve_local_dir('my-repo', str(checkout))

        assert resolved == str(checkout)

    def test_override_rejects_missing_directory(
        self, mounter: Mounter, tmp_path: pathlib.Path
    ) -> None:
        with pytest.raises(Exception, match='No such directory'):
            mounter._resolve_local_dir('my-repo', str(tmp_path / 'absent'))

    def test_without_override_uses_dev_dir(self, mounter: Mounter) -> None:
        with patch.object(
            Mounter, '_find_local_repo_name', return_value='wazo-my-repo'
        ):
            resolved = mounter._resolve_local_dir('my-repo', None)

        assert resolved == '/local/src/wazo-my-repo'


class TestStopSyncWaitsForExit:
    def _mount(self, tmp_path: pathlib.Path, pid: int = 99999) -> dict[str, str]:
        pid_file = tmp_path / 'lsyncd.pid'
        pid_file.write_text(str(pid))
        return {
            'project': 'my-repo',
            'lsync_config': str(tmp_path / 'config'),
            'lsync_pidfile': str(pid_file),
            'local_path': '/local/src/my-repo',
        }

    def test_waits_until_lsyncd_exits(
        self,
        mounter: Mounter,
        config: MagicMock,
        state: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        config.rsync_only = False
        state.get_mount.return_value = self._mount(tmp_path)

        with patch(
            'wazo_sdk.mount.is_lsyncd_pid', side_effect=[True, True, True, False]
        ) as is_lsyncd:
            with patch('os.kill') as kill:
                mounter._stop_sync('my-repo')

        assert kill.call_args_list == [call(99999, signal.SIGTERM)]
        assert is_lsyncd.call_count == 4

    def test_escalates_to_sigkill_when_lsyncd_does_not_exit(
        self,
        mounter: Mounter,
        config: MagicMock,
        state: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        config.rsync_only = False
        state.get_mount.return_value = self._mount(tmp_path)

        with patch('wazo_sdk.mount.is_lsyncd_pid', return_value=True):
            with patch('wazo_sdk.mount.LSYNCD_STOP_TIMEOUT', 0.05):
                with patch('wazo_sdk.mount.LSYNCD_STOP_POLL_INTERVAL', 0.01):
                    with patch('os.kill') as kill:
                        mounter._stop_sync('my-repo')

        assert call(99999, signal.SIGTERM) in kill.call_args_list
        assert call(99999, signal.SIGKILL) in kill.call_args_list

    def test_does_not_kill_a_pid_that_is_not_lsyncd(
        self,
        mounter: Mounter,
        config: MagicMock,
        state: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        config.rsync_only = False
        state.get_mount.return_value = self._mount(tmp_path)

        with patch('wazo_sdk.mount.is_lsyncd_pid', return_value=False):
            with patch('os.kill') as kill:
                mounter._stop_sync('my-repo')

        kill.assert_not_called()

    def test_still_cleans_up_when_pid_is_not_lsyncd(
        self,
        mounter: Mounter,
        config: MagicMock,
        state: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        config.rsync_only = False
        mount = self._mount(tmp_path)
        state.get_mount.return_value = mount

        with patch('wazo_sdk.mount.is_lsyncd_pid', return_value=False):
            with patch('os.kill'):
                mounter._stop_sync('my-repo')

        assert not pathlib.Path(mount['lsync_pidfile']).exists()


class TestUmountState:
    def test_removes_state_after_stopping_the_sync(
        self, mounter: Mounter, config: MagicMock, state: MagicMock
    ) -> None:
        config.get_project_name.return_value = 'my-repo'
        state.is_mounted.return_value = True

        with patch.object(Mounter, '_unapply_mount'):
            with patch.object(Mounter, '_stop_sync') as stop_sync:
                mounter.umount('my-repo')

        stop_sync.assert_called_once_with('my-repo')
        state.remove_mount.assert_called_once_with('test-host', 'my-repo')

    def test_does_not_touch_state_when_nothing_is_mounted(
        self, mounter: Mounter, config: MagicMock, state: MagicMock
    ) -> None:
        config.get_project_name.return_value = 'my-repo'
        state.is_mounted.return_value = False

        with patch.object(Mounter, '_unapply_mount'):
            with patch.object(Mounter, '_stop_sync') as stop_sync:
                mounter.umount('my-repo')

        stop_sync.assert_not_called()
        state.remove_mount.assert_not_called()


class TestSwitchCheckoutFailure:
    def test_failed_start_keeps_the_mount_in_state(
        self, mounter: Mounter, config: MagicMock, state: MagicMock
    ) -> None:
        # stopping the old sync must not make wdk forget the mount: the remote
        # bind mounts and develop install are still in place
        config.rsync_only = False
        config.get_project_name.return_value = 'my-repo'
        state.get_mount.return_value = {
            'project': 'my-repo',
            'lsync_config': None,
            'lsync_pidfile': None,
            'local_path': '/local/src/old-checkout',
        }

        with patch.object(Mounter, '_is_sync_running', return_value=True):
            with patch.object(
                Mounter, '_resolve_local_dir', return_value='/local/src/new'
            ):
                with patch.object(
                    Mounter, '_start_sync', side_effect=SyncError('boom')
                ):
                    with pytest.raises(SyncError):
                        mounter.mount('my-repo', '/local/src/new')

        state.remove_mount.assert_not_called()
