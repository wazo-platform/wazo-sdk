#!/usr/bin/env bats

load helpers.bash

setup_file() {
    build_image
}

setup() {
    common_setup
    setup_proxy_jump
}

teardown() {
    kill_lsyncd_from_cache
    common_teardown
    unset WDK_HOSTNAME PROXY_JUMP WDK_RSYNC_ONLY
}

@test "mount reaches a host only the proxy jump can reach" {
    run_wdk --proxy-jump "$PROXY_JUMP" mount wazo-test-service

    docker_exec test -f /usr/src/wazo/wazo-test-service/setup.py
    run docker_exec pip3 show wazo-test-service
    [ "$status" -eq 0 ]
}

@test "mount without the proxy jump does not reach that host" {
    run_wdk mount wazo-test-service

    run docker_exec test -e /usr/src/wazo/wazo-test-service/setup.py
    [ "$status" -ne 0 ]
}

@test "lsyncd syncs through the proxy jump" {
    require_lsyncd
    export WDK_RSYNC_ONLY=false

    run_wdk --proxy-jump "$PROXY_JUMP" mount wazo-test-service

    wait_for_remote_content /usr/src/wazo/wazo-test-service/etc/wazo-test-service/config.yml "test_key: test_value"
}

@test "restart goes through the proxy jump" {
    run_wdk --proxy-jump "$PROXY_JUMP" restart wazo-test-service

    run docker_exec cat /var/log/mock-systemctl.log
    [[ "$output" == *"systemctl restart wazo-test-service"* ]]
}
