#!/bin/bash -e
set -o pipefail

# Run from inside the e2e-local docker container. Once an individual spec passes, it's cached and
# not re-run. Set CLEAN to run all tests even if they passed previously.

source /ella/scripts/bash-util.sh
touch_dir=/tmp/e2e
APP_URL=${APP_URL:-127.0.0.1:28752}
CHROME_HOST=${CHROME_HOST:-172.17.0.1}
E2E_PARAMS=(--baseUrl "${APP_URL}" --hostname "${CHROME_HOST}" --port 4444 --path "/")
mapfile -t ALL_SPECS < <(ls src/webui/tests/e2e/tests/*.js)
export DEBUG=true
SKIP=()
PASS=()

log() {
    echo "$(date +%Y-%m-%d\ %H:%M:%S) - $*" >&2
}

err() {
    log "${RED}ERROR${RESET} - $*"
}

time_delta() {
    local start=$1
    local end=$2
    local diff=$((end - start))
    local sec=$((diff % 60))
    local min=$((diff / 60))
    printf "%dm%02ds\n" $min $sec
}

init_tests() {
    mkdir -p $touch_dir
    if [[ -n $CLEAN ]] && ls $touch_dir/* &>/dev/null; then
        echo "Resetting"
        rm $touch_dir/*
    fi
    if [[ -n $HEADLESS ]]; then
        log "Attempting headless mode"
        unset DEBUG
    fi
}

init_db() {
    while ! pg_isready --dbname=postgres --username=postgres; do
        sleep 2
    done
    createdb e2e-tmp
    DB_URL='postgresql:///e2e-tmp' /ella/ops/test/reset_testdata.py --testset e2e
    pg_dump e2e-tmp --no-owner >/ella/e2e-test-dump.sql
    dropdb e2e-tmp
}

test_spec() {
    local sname touchfile
    sname=$(basename "$*")
    touchfile=$touch_dir/$sname
    if [[ ! -e $touchfile ]]; then
        log "Running $sname"
        if yarn wdio run wdio.conf.js "${E2E_PARAMS[@]}" --spec "$sname"; then
            touch "$touch_dir/$sname"
            PASS+=("$sname")
        else
            rc=$?
            err "FAILED: $sname"
            return $rc
        fi
    else
        log "Skipping $sname, already passed"
        SKIP+=("$sname")
    fi
}

start=$(date +%s)
init_tests
init_db

if [[ -n ${SPEC:-} ]]; then
    ALL_SPECS=("$SPEC")
    rm -f "$touch_dir/$SPEC"
fi

for spec_path in "${ALL_SPECS[@]}"; do
    log "Checking spec $((${#SKIP[@]} + ${#PASS[@]} + 1)) of ${#ALL_SPECS[@]}"
    test_spec "$spec_path"
done
finish=$(date +%s)

log "Finished running all e2e tests in $(time_delta "$start" "$finish")"
log "SKIP: ${#SKIP[@]}"
log "PASS: ${#PASS[@]}"
