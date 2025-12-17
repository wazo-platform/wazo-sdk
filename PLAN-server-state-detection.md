# Implementation Plan: Server-Side State Detection for wdk

## Problem Statement

The `wdk mount` command relies on a local state file (`~/.local/cache/wdk/state`) to track active mounts. This can become desynchronized with actual server state when:

- State file is corrupted or deleted
- `umount` command fails partially (e.g., network interruption mid-cleanup)
- Manual intervention on the server
- Multiple clients mounting to the same server

## Solution Overview

Implement server-side detection using:
1. `pip list -v -e --format=json` - detect editable Python installs
2. `findmnt` / `mount` - detect bind mounts from source directory

This allows the tool to query actual server state and reconcile with local state.

---

## Implementation Steps

### Phase 1: Server State Detection Module

#### Step 1.1: Create `wazo_sdk/server_state.py`

New module to query server-side mount state via SSH.

```python
class ServerState:
    def __init__(self, hostname: str, remote_source: str, logger: Logger)

    def get_editable_installs(self) -> dict[str, EditableInstall]
        """Query pip list -v -e --format=json, filter to remote_source prefix"""

    def get_bind_mounts(self) -> dict[str, list[BindMount]]
        """Query findmnt --json, filter to remote_source prefix"""

    def get_mounted_projects(self) -> dict[str, ServerMountInfo]
        """Combine editable installs + bind mounts into unified view"""

    def detect_project_state(self, project_name: str) -> ServerMountInfo | None
        """Get state for a specific project"""
```

**Data structures:**
```python
class EditableInstall(TypedDict):
    name: str
    version: str
    location: str  # e.g., /usr/src/wazo/wazo-auth

class BindMount(TypedDict):
    source: str      # e.g., /usr/src/wazo/wazo-auth/etc/wazo-auth/config.yml
    destination: str # e.g., /etc/wazo-auth/config.yml

class ServerMountInfo(TypedDict):
    project: str
    has_editable_install: bool
    editable_location: str | None
    bind_mounts: list[BindMount]
    expected_bind_mounts: list[BindMount]  # from project.yml
    is_complete: bool  # all expected mounts present
```

#### Step 1.2: Implement SSH command execution

Reuse pattern from `service.py` using `sh.ssh.bake()`:

```python
def _run_ssh_command(self, command: str) -> str:
    ssh = sh.ssh.bake(self._hostname)
    return str(ssh(command))
```

#### Step 1.3: Implement `get_editable_installs()`

```python
def get_editable_installs(self) -> dict[str, EditableInstall]:
    output = self._run_ssh_command('pip list -v -e --format=json')
    packages = json.loads(output)

    result = {}
    for pkg in packages:
        location = pkg.get('editable_project_location') or pkg.get('location', '')
        if location.startswith(self._remote_source):
            # Extract project name from path
            project = location.removeprefix(self._remote_source).strip('/')
            result[project] = EditableInstall(
                name=pkg['name'],
                version=pkg['version'],
                location=location
            )
    return result
```

#### Step 1.4: Implement `get_bind_mounts()`

```python
def get_bind_mounts(self) -> dict[str, list[BindMount]]:
    # Use findmnt for structured output
    output = self._run_ssh_command('findmnt --json -t none 2>/dev/null || echo "{}"')
    data = json.loads(output)

    result: dict[str, list[BindMount]] = {}
    for fs in data.get('filesystems', []):
        source = fs.get('source', '')
        # Bind mounts show as /dev/xxx[/path] - extract the path
        if '[' in source and self._remote_source in source:
            # Parse source path from bracket notation
            actual_source = source.split('[')[1].rstrip(']')
            if actual_source.startswith(self._remote_source):
                # Extract project name
                rel_path = actual_source.removeprefix(self._remote_source).strip('/')
                project = rel_path.split('/')[0]

                mount = BindMount(source=actual_source, destination=fs['target'])
                result.setdefault(project, []).append(mount)

    return result
```

**Alternative approach using `mount` command (fallback):**
```python
def _get_bind_mounts_fallback(self) -> dict[str, list[BindMount]]:
    output = self._run_ssh_command('mount -t none')
    # Parse: /usr/src/wazo/proj/file on /etc/proj/file type none (rw,bind)
    ...
```

---

### Phase 2: Integrate with Mounter Class

#### Step 2.1: Add ServerState to Mounter

Modify `wazo_sdk/mount.py`:

```python
from wazo_sdk.server_state import ServerState

class Mounter:
    def __init__(self, logger: Logger, config: Config, state: State) -> None:
        # ... existing code ...
        self._server_state = ServerState(
            self._hostname,
            self._remote_dir,
            logger
        )
```

#### Step 2.2: Enhance `_is_mounted_and_running()`

Current implementation only checks local state. Add server-side check:

```python
def _is_mounted_and_running(self, repo_name: str) -> bool:
    # Check local state first (fast path)
    mount = self._state.get_mount(self._hostname, repo_name)
    if mount and self._is_sync_running(mount):
        return True

    # Fall back to server-side detection
    server_mount = self._server_state.detect_project_state(repo_name)
    return server_mount is not None and server_mount['has_editable_install']
```

#### Step 2.3: Enhance `umount()` to work without local state

Current `umount()` fails if local state is missing. Modify to detect from server:

```python
def umount(self, repo_name: str) -> None:
    # ... validation ...
    real_repo_name = self._config.get_project_name(repo_name)
    repo_config = self._config.get_project(real_repo_name)

    # Check if mounted on server (regardless of local state)
    server_mount = self._server_state.detect_project_state(real_repo_name)

    if server_mount or self._is_mounted(real_repo_name):
        self._unapply_mount(real_repo_name, repo_config)

    # Stop local sync if we have state for it
    if self._is_mounted(real_repo_name):
        self._stop_sync(real_repo_name)
    elif server_mount:
        self.logger.info('Cleaned server state for %s (no local sync state)', real_repo_name)
```

#### Step 2.4: Enhance `list_()` to show server state

```python
def list_(self) -> Generator[tuple[str, bool, bool], None, None]:
    """Yields (project, local_sync_running, server_mounted)"""

    # Get local state
    local_mounts = self._state.get_mounts(self._hostname)

    # Get server state
    server_mounts = self._server_state.get_mounted_projects()

    # Merge both views
    all_projects = set(local_mounts.keys()) | set(server_mounts.keys())

    for project in sorted(all_projects):
        local_mount = local_mounts.get(project)
        local_running = self._is_sync_running(local_mount) if local_mount else False
        server_mounted = project in server_mounts

        yield project, local_running, server_mounted
```

---

### Phase 3: New Commands for State Management

#### Step 3.1: Create `wazo_sdk/commands/state.py`

```python
class StateShow(Command):
    """Show mount state from both local and server perspectives"""

    def take_action(self, parsed_args):
        # Display comparison table:
        # Project | Local Sync | Server Editable | Server Binds | Status
        # wazo-auth | Running | Yes | 1/1 | OK
        # wazo-confd | Stopped | Yes | 0/2 | PARTIAL
        # wazo-dird | None | Yes | 2/2 | ORPHAN (no local state)

class StateSync(Command):
    """Reconcile local state with server state"""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument('--dry-run', action='store_true')
        return parser

    def take_action(self, parsed_args):
        # 1. Detect orphaned server mounts (server has, local doesn't)
        # 2. Detect stale local state (local has, server doesn't)
        # 3. Optionally clean up both

class StateClean(Command):
    """Clean orphaned mounts from server"""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('repos', nargs='*')
        return parser

    def take_action(self, parsed_args):
        # For each orphaned mount on server:
        # 1. pip uninstall / setup.py develop --uninstall
        # 2. umount bind mounts
        # 3. rm cleanup files
```

#### Step 3.2: Register new commands in `setup.py`

```python
'wazo_sdk.commands': [
    # ... existing ...
    'state_show = wazo_sdk.commands.state:StateShow',
    'state_sync = wazo_sdk.commands.state:StateSync',
    'state_clean = wazo_sdk.commands.state:StateClean',
],
```

---

### Phase 4: Enhance Existing Commands

#### Step 4.1: Update `Mount` command output

Show server state detection results:

```
$ wdk mount wazo-auth
wazo-auth: already mounted on server (detected via pip list)
wazo-auth: syncing local changes...
wazo-auth: bind mount /etc/wazo-auth/config.yml already present
```

#### Step 4.2: Update `Umount` command with `--force` flag

```python
class Umount(Command):
    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument('repos', nargs='*')
        parser.add_argument('-r', '--restart', action='store_true')
        parser.add_argument(
            '--force',
            action='store_true',
            help='Clean server state even if local state is missing'
        )
        return parser
```

#### Step 4.3: Add `--server-only` flag to info/list

```
$ wdk mount --list --server-only
Projects mounted on server (detected):
  wazo-auth (editable install + 1 bind mount)
  wazo-confd (editable install + 2 bind mounts)
```

---

### Phase 5: Error Handling and Edge Cases

#### Step 5.1: Handle SSH failures gracefully

```python
class ServerState:
    def get_mounted_projects(self) -> dict[str, ServerMountInfo]:
        try:
            # ... detection logic ...
        except sh.ErrorReturnCode as e:
            self._logger.warning('Failed to query server state: %s', e)
            return {}  # Fall back to local-only mode
```

#### Step 5.2: Handle partial mount states

A project might have:
- Editable install but missing bind mounts (partial mount)
- Bind mounts but no editable install (manual intervention?)
- Stale cleanup files from failed umount

Detection should flag these inconsistencies.

#### Step 5.3: Handle unknown projects

Server may have editable installs for projects not in local `project.yml`:

```python
def get_mounted_projects(self) -> dict[str, ServerMountInfo]:
    # Include projects even if not in project.yml
    # Mark them as "unknown" so user can decide what to do
```

---

## File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `wazo_sdk/server_state.py` | **New** | Server state detection module |
| `wazo_sdk/mount.py` | Modify | Integrate ServerState, enhance methods |
| `wazo_sdk/commands/state.py` | **New** | State management commands |
| `wazo_sdk/commands/mount.py` | Modify | Add --force flag, improve output |
| `setup.py` | Modify | Register new commands |

---

## Testing Strategy

1. **Unit tests for server_state.py**
   - Mock SSH responses for pip list and findmnt
   - Test parsing edge cases (empty results, malformed JSON)

2. **Integration tests**
   - Test with actual Wazo dev server
   - Verify detection matches actual state

3. **Manual testing scenarios**
   - Delete local state file, verify umount still works
   - Partial mount failure, verify detection shows inconsistency
   - Multiple mounts, verify all detected

---

## Migration / Compatibility

- Existing local state file format unchanged
- New server detection is additive, not replacing local state
- Commands work the same by default; new flags opt-in to server detection features
- No breaking changes to existing workflows
