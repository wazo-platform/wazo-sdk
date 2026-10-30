#!/usr/bin/env bats

load helpers.bash

setup_file() {
    build_image
}

setup() {
    common_setup
    run_wdk mount wazo-test-service
}

teardown() {
    common_teardown
}

@test "umount removes bind mounts" {
    run docker_exec mount
    [[ "$output" == *"/etc/wazo-test-service/config.yml"* ]]

    run_wdk umount wazo-test-service

    run docker_exec mount
    [[ "$output" != *"/etc/wazo-test-service/config.yml"* ]]
}

@test "umount runs setup.py develop --uninstall" {
    run docker_exec pip3 show wazo-test-service
    [ "$status" -eq 0 ]

    run_wdk umount wazo-test-service

    run docker_exec pip3 show wazo-test-service
    [ "$status" -ne 0 ]
}

@test "umount removes state entry" {
    run_wdk umount wazo-test-service

    [ -z "$(state_mount wazo-test-service)" ]
}

@test "umount cleans specified files" {
    docker_exec touch /usr/local/bin/wazo-test-service

    run_wdk umount wazo-test-service

    run docker_exec test -e /usr/local/bin/wazo-test-service
    [ "$status" -ne 0 ]
}
