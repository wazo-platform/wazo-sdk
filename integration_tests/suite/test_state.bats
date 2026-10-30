#!/usr/bin/env bats

load helpers.bash

setup_file() {
    build_image
}

setup() {
    common_setup
}

teardown() {
    common_teardown
}

@test "state file created on first mount" {
    local state_file="$WDK_CACHE_DIR/state"
    [ ! -f "$state_file" ]

    run_wdk mount wazo-test-service

    [ -f "$state_file" ]
}

@test "state file records mounted repo" {
    run_wdk mount wazo-test-service

    local state_file="$WDK_CACHE_DIR/state"
    run cat "$state_file"
    [[ "$output" == *"wazo-test-service"* ]]
    [[ "$output" == *"wdk-test-target"* ]]
}

@test "state file empty mounts after mount/umount cycle" {
    run_wdk mount wazo-test-service
    run_wdk umount wazo-test-service

    local state_file="$WDK_CACHE_DIR/state"
    run python3 -c "
import json
with open('$state_file') as f:
    state = json.load(f)
mounts = state.get('hosts', {}).get('wdk-test-target', {}).get('mounts', {})
assert not mounts, f'Expected empty mounts, got {mounts}'
print('ok')
"
    [ "$output" = "ok" ]
}
