#!/bin/bash -e
set -o pipefail

source /ella/scripts/bash-util.sh

TESTDATA_API=http://localhost:23232
SCRIPT_DIR=$(script_dir "${BASH_SOURCE[0]}")
OPS_DIR=$(dirname "$SCRIPT_DIR")
TD_OPS_DIR=$OPS_DIR/testdata
SUPERVISOR_CFG=$OPS_DIR/dev/supervisor.cfg
CMD_LOG=/logs/check_testdata_commands.log

if git -C ella-testdata remote get-url origin | grep -q https://; then
    FETCH_MODE=https
else
    FETCH_MODE=ssh
fi

declare -a ERRS

test_fail() {
    if [[ -n $* ]]; then
        echo -n "$*: "
    fi
    red "FAILED"
    ERRS+=("$*")
}

test_pass() {
    if [[ -n $* ]]; then
        echo -n "$*: "
    fi
    green "OK"
}

curl() {
    log "Running: curl -f $*"
    log_command curl -f "$@"
}

log() {
    echo "$(date -Iseconds) - $*" >&2
}

log_command() {
    log "$*" 2>&1 | tee -a $CMD_LOG
    command "$@"
}

supervisorctl() {
    log_command supervisorctl -c "$SUPERVISOR_CFG" "$@"
}

check_db_reset() {
    local db_status
    set +e
    # returns non-zero when not ready, so ignore errors here
    db_status=$(supervisorctl status dbreset)
    set -e
    echo "$db_status" | grep -qw EXITED
}

api_reset_db() {
    local testset=$1
    declare -a args
    if [[ -n $testset ]]; then
        args=(-d "testset=$testset")
    else
        args=(-X POST)
    fi
    curl "${args[@]}" ${TESTDATA_API}/database/reset
}

api_dump_db() {
    local testset=$1
    curl -d "testset=$testset" ${TESTDATA_API}/database/dump
}

fetch_testdata() {
    log_command python3 "${TD_OPS_DIR}/fetch-testdata.py" --mode ${FETCH_MODE} "$@"
}

testdata_status() {
    fetch_testdata --status
}

check_repo_ref() {
    local ref=$1
    if [[ -z $ref ]]; then
        echo "check_repo_ref: no ref received" >&2
        return 1
    fi
    testdata_status | grep -Eq 'ref:\s+'"$ref"'\b'
}

repo_is_shallow() {
    testdata_status | grep -iEq 'shallow:[[:space:]]+True'
}

###
### general tests
###

mypy /ella/ops/testdata

###
### API tests
###

##### setup

if [[ -S /socket/supervisor.sock ]]; then
    supervisorctl start postgres testdata_api
else
    log "starting new supervisor process"
    supervisord -c "${SUPERVISOR_CFG}" &>/logs/supervisor_test.log &
    # wait for supervisor socket to get created
    sleep 3
    # turn off unnecessary services
    supervisorctl stop webpack web docs polling
fi

# Make sure initial db reset has completed
pg_wait=0
while ! check_db_reset; do
    if ((pg_wait > 15)); then
        log "PostgreSQL still not started after $pg_wait retries. Aborting" >&2
        exit 1
    fi
    log "Waiting for PostgreSQL to start..."
    pg_wait=$((pg_wait + 1))
    sleep 5
done

###### tests

log "basic healthcheck"
curl ${TESTDATA_API}/healthcheck
echo

#

ds_name="testdump_$(date +%s)"

log "dump data"
api_dump_db "${ds_name}"
echo

#

log "attempt duplicate dump"
api_dump_db "${ds_name}"
echo

#

log "delete all local dumps"
curl -X POST $TESTDATA_API/clean
echo

#

log "load now deleted dataset"
if api_reset_db "${ds_name}"; then
    log "passed, but it shouldn't"
    exit 1
else
    log "test failed successfully"
fi
echo

#

log "re-create deleted dump"
api_dump_db "${ds_name}"
echo

#

log "load local dump"
api_reset_db "${ds_name}"
echo

#

log "load e2e dataset"
api_reset_db e2e
echo

#

log "load default dataset"
api_reset_db

#

# cleanup
supervisorctl stop all
echo -e "\n\n"

###
### fetch-testdata tests
###

# check the initial testdata repo status
msg="initial testdata repo status"
if testdata_status; then
    test_pass "$msg"
else
    test_fail "$msg"
fi
echo

# default fetch (should no-op)
msg="fetching current ref testdata"
if fetch_testdata; then
    test_pass "$msg"
else
    test_fail "$msg"
fi
echo

# should be default branch / REF
msg="check testdata ref"
TEST_REF=${TEST_REF:-branch/main}
if check_repo_ref "${TEST_REF}"; then
    test_pass "$msg"
else
    test_fail "$msg: expected ${TEST_REF}"
fi
echo

msg="check repo is shallow"
if repo_is_shallow; then
    test_pass "$msg"
else
    test_fail "$msg"
fi
echo

# clone with explicit ref
msg="clean clone main ref"
if FETCH_MODE=https fetch_testdata --ref main --clean; then
    test_pass "$msg"
else
    test_fail "$msg"
fi

# TODO:
# - move to pytest
#     - this started simple, but we now need a proper testing framework
# - Additional tests
#     - fetch existing refs (branch, tag, commit) from --shallow repo (should fail)
#     - fetch non-existing refs (branch, tag, commit) from --shallow repo (should fail)
#     - fetch (--full/--shallow) without --clean over existing repo (should fail)
#     - fetch (--full/--shallow) with --clean over existing repo
#     - fetch existing refs (branch, tag, commit) from --full repo
#     - fetch non-existing refs (branch, tag, commit) from --full repo (should fail)
#     - fetch without ref with existing ref pointing at branch (should check for updates)
#     - fetch without ref with existing ref pointing at tag/commit (should not check for updates)
#     - add --remove for `rm -rf repo_dir`
#     - fetch with --clean over non-existing repo

if [[ -n ${ERRS[*]} ]]; then
    echo -e "\n\n"
    log "Failed tests:"
    for err in "${ERRS[@]}"; do
        red "$err"
    done
    exit 1
fi
