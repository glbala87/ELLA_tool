#!/bin/bash -e

TESTDATA_API=http://localhost:23232

curl() {
    log "Running: curl -f $*"
    command curl -f "$@"
}

log() {
    echo "$(date -Iseconds) - $*" >&2
}

supervisorctl() {
    command supervisorctl -c /ella/ops/dev/supervisor.cfg "$@"
}

check_db_reset() {
    supervisorctl status dbreset | grep -q EXITED
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

### setup

if [[ -S /socket/supervisor.sock ]]; then
    supervisorctl start postgres testdata_api
else
    log "starting new supervisor process"
    supervisord -c /ella/ops/dev/supervisor.cfg &>/logs/supervisor_test.log &
    # wait for supervisor socket to get created
    sleep 3
    # turn off unnecessary services
    supervisorctl stop webpack web docs polling
fi

###
### tests
###

mypy /ella/ops/testdata

# Make sure initial db reset has completed
pg_wait=0
while ! check_db_reset; do
    if ((pg_wait > 15)); then
        log "PostgreSQL still not started after $pg_wait retries. Aborting" >&2
        exit 1
    fi
    log "Waiting of PostgreSQL to start..."
    pg_wait=$((pg_wait + 1))
    sleep 5
done

log "basic healthcheck"
curl ${TESTDATA_API}/healthcheck
echo

#

log "dump data"
ds_name="testdump_$(date +%s)"
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
