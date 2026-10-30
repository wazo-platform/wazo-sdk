#!/usr/bin/env bash
# Shared helpers for wazo-sdk integration tests

INTEG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUITE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$INTEG_DIR/.." && pwd)"

# Unique per checkout: the default (directory name) is shared by every
# worktree, so concurrent runs would tear down each other's containers.
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-wdk-integ-$(printf '%s' "$PROJECT_ROOT" | cksum | cut -d' ' -f1)}"
export COMPOSE_PROJECT_NAME

SSH_KEY="$INTEG_DIR/ssh_keys/test_id_ed25519"
SSH_OPTS=(-o IdentitiesOnly=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR)

# git cannot store 0600; ssh ignores a group/world-readable identity file
chmod 600 "$SSH_KEY"

export SSH_PUB_KEY
SSH_PUB_KEY="$(cat "$SSH_KEY.pub")"

# ── Docker lifecycle ──

build_image() {
    docker compose -f "$INTEG_DIR/docker-compose.yml" build
}

start_container() {
    docker compose -f "$INTEG_DIR/docker-compose.yml" up -d
    SSH_PORT="$(docker compose -f "$INTEG_DIR/docker-compose.yml" port ssh-target 22 | cut -d: -f2)"
    export SSH_PORT
}

stop_container() {
    docker compose -f "$INTEG_DIR/docker-compose.yml" down -v --remove-orphans
}

# ── Remote access ──

ssh_target() {
    ssh "${SSH_OPTS[@]}" -p "$SSH_PORT" -i "$SSH_KEY" root@127.0.0.1 "$@"
}

docker_exec() {
    docker compose -f "$INTEG_DIR/docker-compose.yml" exec -T ssh-target "$@"
}

# ── Wait for SSH readiness ──

wait_for_ssh() {
    local retries=30 last_error
    while ! last_error="$(ssh_target true 2>&1)"; do
        retries=$((retries - 1))
        if [ "$retries" -le 0 ]; then
            echo "SSH not ready after 30 attempts; last error: $last_error" >&2
            docker compose -f "$INTEG_DIR/docker-compose.yml" logs --tail 20 ssh-target >&2 || true
            return 1
        fi
        sleep 0.5
    done
}

# ── Local fake repo setup ──

create_local_repo() {
    local repo_name="${1:-wazo-test-service}"
    LOCAL_REPO_DIR="$(mktemp -d)"
    export LOCAL_REPO_DIR

    local repo_path="$LOCAL_REPO_DIR/$repo_name"
    mkdir -p "$repo_path/etc/wazo-test-service"

    cat > "$repo_path/setup.py" << 'SETUP'
from setuptools import setup
setup(name='wazo-test-service', version='0.1')
SETUP

    cat > "$repo_path/etc/wazo-test-service/config.yml" << 'CFG'
test_key: test_value
CFG
}

# Creates a checkout outside `local_source`, in a directory NOT named after the
# project, as a git worktree checkout typically is.
create_alternate_checkout() {
    local dir_name="${1:-worktree-ITEM-123}"
    ALT_REPO_DIR="$(mktemp -d)"
    export ALT_REPO_DIR

    ALT_CHECKOUT="$ALT_REPO_DIR/$dir_name"
    export ALT_CHECKOUT

    mkdir -p "$ALT_CHECKOUT/etc/wazo-test-service"

    cat > "$ALT_CHECKOUT/setup.py" << 'SETUP'
from setuptools import setup
setup(name='wazo-test-service', version='0.1')
SETUP

    cat > "$ALT_CHECKOUT/etc/wazo-test-service/config.yml" << 'CFG'
test_key: alternate_value
CFG

    printf 'alternate-checkout' > "$ALT_CHECKOUT/MARKER"
}

# ── SSH wrapper ──
#
# wdk uses `sh.ssh.bake(hostname)` internally, which resolves `ssh` via PATH.
# We place a wrapper script early on PATH that adds `-F <our_config>` to every
# ssh invocation. This avoids touching ~/.ssh/config.

setup_ssh_wrapper() {
    SSH_WRAPPER_DIR="$(mktemp -d)"
    WDK_SSH_CONFIG="$SSH_WRAPPER_DIR/ssh_config"
    export SSH_WRAPPER_DIR WDK_SSH_CONFIG

    cat > "$WDK_SSH_CONFIG" <<EOF
Host wdk-test-target
    HostName 127.0.0.1
    Port ${SSH_PORT}
    User root
    IdentityFile ${SSH_KEY}
    IdentitiesOnly yes
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel ERROR

Host *
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel ERROR
EOF

    local real_ssh
    real_ssh="$(command -v ssh)"
    cat > "$SSH_WRAPPER_DIR/ssh" <<WRAPPER
#!/bin/sh
exec "$real_ssh" -F "$WDK_SSH_CONFIG" "\$@"
WRAPPER
    chmod +x "$SSH_WRAPPER_DIR/ssh"

    export PATH="$SSH_WRAPPER_DIR:$PATH"
}

# ── WDK cache ──

setup_wdk_cache() {
    WDK_CACHE_DIR="$(mktemp -d)"
    export WDK_CACHE_DIR
}

# ── WDK wrapper ──

run_wdk() {
    local project_file="$INTEG_DIR/fixtures/project.yml"
    local config_file="$BATS_TEST_TMPDIR/config.yml"

    cat > "$config_file" <<EOF
remote_source: /usr/src/wazo
rsync_only: ${WDK_RSYNC_ONLY:-true}
cache_dir: $WDK_CACHE_DIR
EOF
    wdk --config "$config_file" \
        --project-file "$project_file" \
        --hostname wdk-test-target \
        --dev-dir "$LOCAL_REPO_DIR" \
        "$@"
}

# ── Remote content polling ──

wait_for_remote_content() {
    local path="$1" expected="$2" retries="${3:-75}"
    while [ "$retries" -gt 0 ]; do
        if [ "$(docker_exec cat "$path" 2>/dev/null)" = "$expected" ]; then
            return 0
        fi
        sleep 0.2
        retries=$((retries - 1))
    done
    echo "timed out waiting for $path to contain: $expected" >&2
    docker_exec cat "$path" >&2 || true
    return 1
}

remote_inode() {
    docker_exec stat -c %i "$1"
}

# ── wdk state and lsyncd pidfile ──

# Without jq, state_mount prints nothing and every "no state recorded"
# assertion would pass; fail setup instead.
require_jq() {
    if ! command -v jq >/dev/null 2>&1; then
        echo "jq is required to run the integration tests" >&2
        return 1
    fi
}

# Prints the mount recorded for <project> as JSON, or nothing if there is none.
# With <field>, prints only that field's value.
state_mount() {
    local state_file="$WDK_CACHE_DIR/state"
    [ -f "$state_file" ] || return 0
    jq -r --arg project "$1" --arg field "${2:-}" '
        .hosts["wdk-test-target"].mounts[$project] // empty
        | select(length > 0)
        | if $field == "" then tojson else .[$field] // empty end
    ' "$state_file"
}

# Prints the first lsyncd pidfile wdk wrote to its cache dir; fails if none.
lsyncd_pidfile() {
    local pidfile
    for pidfile in "$WDK_CACHE_DIR"/*.pid; do
        if [ -f "$pidfile" ]; then
            echo "$pidfile"
            return 0
        fi
    done
    return 1
}

require_lsyncd() {
    if ! command -v lsyncd >/dev/null 2>&1; then
        skip "lsyncd not installed on the test runner"
    fi
}

shadow_lsyncd_with_failure() {
    mkdir -p "$BATS_TEST_TMPDIR/bin"
    printf '#!/bin/sh\nexit 1\n' > "$BATS_TEST_TMPDIR/bin/lsyncd"
    chmod +x "$BATS_TEST_TMPDIR/bin/lsyncd"
    export PATH="$BATS_TEST_TMPDIR/bin:$PATH"
}

kill_lsyncd_from_cache() {
    [ -d "$WDK_CACHE_DIR" ] || return 0
    local pidfile pid
    for pidfile in "$WDK_CACHE_DIR"/*.pid; do
        [ -f "$pidfile" ] || continue
        pid="$(cat "$pidfile" 2>/dev/null)"
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
}

# ── Per-test setup/teardown ──

common_setup() {
    require_jq
    start_container
    wait_for_ssh
    create_local_repo
    setup_ssh_wrapper
    setup_wdk_cache
}

# Zuul's post playbook publishes $WAZO_TEST_DOCKER_LOGS_DIR/* (flat files)
save_container_logs() {
    [ -n "$WAZO_TEST_DOCKER_LOGS_DIR" ] || return 0
    mkdir -p "$WAZO_TEST_DOCKER_LOGS_DIR"
    docker compose -f "$INTEG_DIR/docker-compose.yml" logs --no-color ssh-target \
        > "$WAZO_TEST_DOCKER_LOGS_DIR/$(basename "$BATS_TEST_FILENAME" .bats)-${BATS_TEST_NUMBER}.log" 2>&1 || true
}

common_teardown() {
    save_container_logs
    stop_container
    if [ -n "$LOCAL_REPO_DIR" ]; then rm -rf "$LOCAL_REPO_DIR"; fi
    if [ -n "$ALT_REPO_DIR" ]; then rm -rf "$ALT_REPO_DIR"; fi
    if [ -n "$SSH_WRAPPER_DIR" ]; then rm -rf "$SSH_WRAPPER_DIR"; fi
    if [ -n "$WDK_CACHE_DIR" ]; then rm -rf "$WDK_CACHE_DIR"; fi
}
