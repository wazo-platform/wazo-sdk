#!/usr/bin/env bats

load helpers.bash

setup_file() {
    common_setup_file
}

setup() {
    common_setup
}

teardown() {
    common_teardown
}

@test "mount rsyncs files to remote /usr/src/wazo/<repo>/" {
    run_wdk mount wazo-test-service

    docker_exec test -f /usr/src/wazo/wazo-test-service/setup.py
    docker_exec test -f /usr/src/wazo/wazo-test-service/etc/wazo-test-service/config.yml
}

@test "mount runs setup.py develop for python3 projects" {
    run_wdk mount wazo-test-service

    run docker_exec pip3 show wazo-test-service
    [ "$status" -eq 0 ]
    [[ "$output" == *"Editable project location: /usr/src/wazo/wazo-test-service"* ]]
}

@test "mount creates bind mounts" {
    run_wdk mount wazo-test-service

    # The bind entry maps etc/wazo-test-service/config.yml -> /etc/wazo-test-service/config.yml
    run docker_exec mount
    [[ "$output" == *"/etc/wazo-test-service/config.yml"* ]]
}

@test "mount with missing dest creates placeholder before binding" {
    run docker_exec test -e /etc/wazo-test-service/config.yml
    [ "$status" -ne 0 ]

    run_wdk mount wazo-test-service

    # After mount, the dest should exist and be a bind mount
    docker_exec test -e /etc/wazo-test-service/config.yml
    run docker_exec mount
    [[ "$output" == *"/etc/wazo-test-service/config.yml"* ]]
}

@test "mount --list shows mounted repo" {
    run_wdk mount wazo-test-service

    run run_wdk mount --list
    [[ "$output" == *"wazo-test-service"* ]]
}

@test "mount does not record state when rsync fails" {
    stop_container

    run run_wdk mount wazo-test-service
    [ "$status" -ne 0 ]

    local state_file="$WDK_CACHE_DIR/state"
    run python3 -c "
import json, sys
if not __import__('os').path.exists('$state_file'):
    sys.exit(0)
with open('$state_file') as f:
    state = json.load(f)
mounts = state.get('hosts', {}).get('wdk-test-target', {}).get('mounts', {})
assert not mounts, f'expected no mounts recorded, got {mounts}'
"
    [ "$status" -eq 0 ]
}

@test "mount is idempotent (second mount does not fail)" {
    run_wdk mount wazo-test-service
    run_wdk mount wazo-test-service

    docker_exec test -f /usr/src/wazo/wazo-test-service/setup.py
    run docker_exec mount
    [[ "$output" == *"/etc/wazo-test-service/config.yml"* ]]
}
