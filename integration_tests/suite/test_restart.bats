#!/usr/bin/env bats

setup_file() {
    load helpers.bash
    common_setup_file
}

setup() {
    load helpers.bash
    common_setup
}

teardown() {
    load helpers.bash
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
