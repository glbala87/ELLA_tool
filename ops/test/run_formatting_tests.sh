#!/bin/bash -e

pushd /ella
source ./scripts/bash-util.sh

log() {
    local color=$1
    echo -n "$(date '+%Y-%m-%d %H:%M:%S') "
    $color "${@:2}"
}

fail() {
    local name=$1
    FAILED+=("$name")
    log red "### $name: FAILED ###"
}

pass() {
    local name=$1
    PASSED+=("$name")
    log green "### $name: SUCCESS ###"
}

FAILED=()
PASSED=()
run() {
    if [[ "$1" == yarn ]]; then
        local name=$2
    else
        local name=$1
    fi
    log magenta "Running ${name}"
    if ! "$@"; then
        fail "$name"
    else
        pass "$name"
    fi
}

run black --check /ella
run mypy /ella/src
run flake8
run yarn prettier -l '**/*\.@(js|scss|json|css|html|yml)'
run yarn eslint /ella

log red "FAILED: ${FAILED[*]}"
log green "PASSED: ${PASSED[*]}"
exit ${#FAILED}
