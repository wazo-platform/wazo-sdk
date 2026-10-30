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

@test "restart invokes systemctl restart via mock" {
    run_wdk restart wazo-test-service

    run docker_exec cat /var/log/mock-systemctl.log
    [[ "$output" == *"systemctl restart wazo-test-service"* ]]
}

@test "mount -r mounts and restarts service" {
    run_wdk mount -r wazo-test-service

    docker_exec test -f /usr/src/wazo/wazo-test-service/setup.py
    run docker_exec cat /var/log/mock-systemctl.log
    [[ "$output" == *"systemctl restart wazo-test-service"* ]]
}
