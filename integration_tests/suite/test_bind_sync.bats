#!/usr/bin/env bats
#
# lsyncd syncs with rsync's default write-to-temp-then-rename strategy, which
# replaces the destination inode. A bind mount created from the old inode keeps
# resolving to it, so the bind-mounted copy goes stale on the first local edit.

load helpers.bash

LOCAL_CONFIG_REL=etc/wazo-test-service/config.yml
REMOTE_SRC=/usr/src/wazo/wazo-test-service/etc/wazo-test-service/config.yml
BIND_DEST=/etc/wazo-test-service/config.yml

setup_file() {
    build_image
}

setup() {
    require_lsyncd
    export WDK_RSYNC_ONLY=false
    common_setup
}

teardown() {
    kill_lsyncd_from_cache
    common_teardown
    unset WDK_RSYNC_ONLY
}

local_config_path() {
    echo "$LOCAL_REPO_DIR/wazo-test-service/$LOCAL_CONFIG_REL"
}

@test "lsyncd propagates a local edit to the bind-mounted file" {
    skip "stale bind mount after rsync rename; fixed by fix/rebind-stale-file-binds"

    run_wdk mount wazo-test-service

    run docker_exec mount
    [[ "$output" == *"$BIND_DEST"* ]]

    run docker_exec cat "$BIND_DEST"
    [ "$output" = "test_key: test_value" ]

    printf 'test_key: modified_value\n' > "$(local_config_path)"

    wait_for_remote_content "$REMOTE_SRC" "test_key: modified_value"

    run docker_exec cat "$BIND_DEST"
    echo "bind mount shows: $output" >&2
    [ "$output" = "test_key: modified_value" ]
}

@test "lsyncd sync keeps the bind mount and its source on the same inode" {
    skip "stale bind mount after rsync rename; fixed by fix/rebind-stale-file-binds"

    run_wdk mount wazo-test-service

    local before
    before="$(remote_inode "$REMOTE_SRC")"
    [ "$before" = "$(remote_inode "$BIND_DEST")" ]

    printf 'test_key: modified_value\n' > "$(local_config_path)"

    wait_for_remote_content "$REMOTE_SRC" "test_key: modified_value"

    local after_src after_dest
    after_src="$(remote_inode "$REMOTE_SRC")"
    after_dest="$(remote_inode "$BIND_DEST")"
    echo "inode before: $before, source after: $after_src, bind mount after: $after_dest" >&2
    [ "$after_src" = "$after_dest" ]
}
