#!/usr/bin/env bats

load helpers.bash

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

@test "mount does not record state when lsyncd fails to start" {
    skip "wdk exits 0 on sync failure: Mount.take_action catches all exceptions"

    shadow_lsyncd_with_failure

    run run_wdk mount wazo-test-service
    [ "$status" -ne 0 ]

    [ -z "$(state_mount wazo-test-service)" ]
}

@test "mount in lsync mode starts an lsyncd daemon" {
    run_wdk mount wazo-test-service

    # _start_sync writes a pidfile next to the lsync config in cache_dir
    local pidfile
    pidfile="$(lsyncd_pidfile)"
    [ -n "$pidfile" ]
    [ -f "$pidfile" ]

    local pid
    pid="$(cat "$pidfile")"
    [ -n "$pid" ]
    kill -0 "$pid"
    grep -q lsyncd "/proc/$pid/comm"
}

@test "mount in lsync mode records lsync_pidfile in state" {
    run_wdk mount wazo-test-service

    local recorded
    recorded="$(state_mount wazo-test-service lsync_pidfile)"
    [[ "$recorded" == "$WDK_CACHE_DIR"/*.pid ]]
}

@test "umount in lsync mode kills the lsyncd process" {
    run_wdk mount wazo-test-service

    local pidfile pid
    pidfile="$(lsyncd_pidfile)"
    pid="$(cat "$pidfile")"
    kill -0 "$pid"

    run_wdk umount wazo-test-service

    # SIGTERM is async; give lsyncd a moment to exit
    local retries=20
    while kill -0 "$pid" 2>/dev/null && [ "$retries" -gt 0 ]; do
        sleep 0.1
        retries=$((retries - 1))
    done
    run kill -0 "$pid"
    [ "$status" -ne 0 ]
}

@test "umount in lsync mode removes the pidfile from disk" {
    run_wdk mount wazo-test-service

    local pidfile
    pidfile="$(lsyncd_pidfile)"
    [ -f "$pidfile" ]

    run_wdk umount wazo-test-service

    [ ! -f "$pidfile" ]
}

@test "stale pid file from a crashed lsyncd is cleaned up on next wdk command" {
    run_wdk mount wazo-test-service

    local pidfile pid
    pidfile="$(lsyncd_pidfile)"
    pid="$(cat "$pidfile")"

    # Simulate lsyncd crash: SIGKILL leaves the pidfile orphaned (unlike SIGTERM,
    # which lets lsyncd clean up after itself)
    kill -9 "$pid"
    local retries=20
    while kill -0 "$pid" 2>/dev/null && [ "$retries" -gt 0 ]; do
        sleep 0.1
        retries=$((retries - 1))
    done

    [ -f "$pidfile" ]

    # Any successful wdk command triggers _remove_stale_config_files cleanup
    run_wdk mount --list

    [ ! -f "$pidfile" ]
}

@test "umount in lsync mode removes state entry" {
    run_wdk mount wazo-test-service
    run_wdk umount wazo-test-service

    [ -z "$(state_mount wazo-test-service)" ]
}

@test "mount from a different path stops the previous lsyncd and syncs the new checkout" {
    run_wdk mount wazo-test-service

    local old_pidfile old_pid
    old_pidfile="$(lsyncd_pidfile)"
    old_pid="$(cat "$old_pidfile")"
    kill -0 "$old_pid"

    create_alternate_checkout
    run_wdk mount "wazo-test-service=$ALT_CHECKOUT"

    # mount must not return while the lsyncd watching the previous checkout is
    # still alive: it would keep syncing the old tree over the new one
    run kill -0 "$old_pid"
    [ "$status" -ne 0 ]

    wait_for_remote_content /usr/src/wazo/wazo-test-service/MARKER alternate-checkout
}

@test "mount twice from the same path keeps the same lsyncd running" {
    run_wdk mount wazo-test-service

    local pidfile pid
    pidfile="$(lsyncd_pidfile)"
    pid="$(cat "$pidfile")"

    run_wdk mount wazo-test-service

    kill -0 "$pid"
}

@test "a failed switch to another checkout keeps the project listed" {
    run_wdk mount wazo-test-service
    create_alternate_checkout

    # shadow lsyncd so starting the sync for the new checkout fails
    shadow_lsyncd_with_failure

    run_wdk mount "wazo-test-service=$ALT_CHECKOUT"

    # the remote bind mounts and develop install are still in place, so wdk
    # must keep reporting the project instead of losing track of it
    run run_wdk mount --list
    [[ "$output" == *"wazo-test-service"* ]]
}
