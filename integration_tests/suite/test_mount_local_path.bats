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

@test "mount <project>=<path> syncs from the given path" {
    create_alternate_checkout

    run_wdk mount "wazo-test-service=$ALT_CHECKOUT"

    docker_exec test -f /usr/src/wazo/wazo-test-service/MARKER
    run docker_exec cat /usr/src/wazo/wazo-test-service/etc/wazo-test-service/config.yml
    [[ "$output" == *"alternate_value"* ]]
}

@test "mount <project>=<path> keeps the remote path keyed on the project name" {
    create_alternate_checkout

    run_wdk mount "wazo-test-service=$ALT_CHECKOUT"

    docker_exec test -d /usr/src/wazo/wazo-test-service
    run docker_exec test -e /usr/src/wazo/worktree-ITEM-123
    [ "$status" -ne 0 ]
}

@test "mount <project>=<path> still applies the project configuration" {
    create_alternate_checkout

    run_wdk mount "wazo-test-service=$ALT_CHECKOUT"

    run docker_exec pip3 show wazo-test-service
    [ "$status" -eq 0 ]
    [[ "$output" == *"Editable project location: /usr/src/wazo/wazo-test-service"* ]]

    run docker_exec mount
    [[ "$output" == *"/etc/wazo-test-service/config.yml"* ]]
}

@test "mount <project>=<path> resolves the project through the usual prefixes" {
    create_alternate_checkout

    run_wdk mount "test-service=$ALT_CHECKOUT"

    docker_exec test -f /usr/src/wazo/wazo-test-service/MARKER
}

@test "mount <project>=<path> records the override in state" {
    create_alternate_checkout

    run_wdk mount "wazo-test-service=$ALT_CHECKOUT"

    [ "$(state_mount wazo-test-service local_path)" = "$ALT_CHECKOUT" ]
}

@test "mount without override records the default local path in state" {
    run_wdk mount wazo-test-service

    [ "$(state_mount wazo-test-service local_path)" = "$LOCAL_REPO_DIR/wazo-test-service" ]
}

@test "mount --list reports the mounted checkout path" {
    create_alternate_checkout

    run_wdk mount "wazo-test-service=$ALT_CHECKOUT"

    run run_wdk mount --list
    [[ "$output" == *"wazo-test-service"* ]]
    [[ "$output" == *"$ALT_CHECKOUT"* ]]
}

@test "mount <project>=<path> expands a user-relative path" {
    create_alternate_checkout

    export HOME="$ALT_REPO_DIR"
    run_wdk mount "wazo-test-service=~/worktree-ITEM-123"

    docker_exec test -f /usr/src/wazo/wazo-test-service/MARKER
}

@test "mount with a nonexistent path records no state" {
    run run_wdk mount "wazo-test-service=$BATS_TEST_TMPDIR/does-not-exist"

    [ -z "$(state_mount wazo-test-service)" ]
}

@test "mount with a nonexistent path does not sync anything" {
    run run_wdk mount "wazo-test-service=$BATS_TEST_TMPDIR/does-not-exist"

    run docker_exec test -e /usr/src/wazo/wazo-test-service/setup.py
    [ "$status" -ne 0 ]
}

@test "umount works on a repo mounted from an overridden path" {
    create_alternate_checkout
    run_wdk mount "wazo-test-service=$ALT_CHECKOUT"

    run_wdk umount wazo-test-service

    run docker_exec mount
    [[ "$output" != *"/etc/wazo-test-service/config.yml"* ]]

    [ -z "$(state_mount wazo-test-service)" ]
}

@test "remounting from a different path re-syncs from the new checkout" {
    run_wdk mount wazo-test-service
    docker_exec test -f /usr/src/wazo/wazo-test-service/setup.py

    create_alternate_checkout
    run_wdk mount "wazo-test-service=$ALT_CHECKOUT"

    docker_exec test -f /usr/src/wazo/wazo-test-service/MARKER

    [ "$(state_mount wazo-test-service local_path)" = "$ALT_CHECKOUT" ]
}
