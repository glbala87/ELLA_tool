#!/bin/bash -e
# Build web assets and then run e2e tests

# shellcheck disable=1091
source ./scripts/bash-util.sh

if [[ -z "${APP_URL}" ]]; then
    yellow "Assuming app is running at 127.0.0.1:28752"
    APP_URL="127.0.0.1:28752"
else
    yellow "Running tests against $APP_URL Ip address to chrome browser"
fi

if [[ -z "${CHROME_HOST}" ]]; then
    yellow "CHROME_HOST not set, using 172.17.0.1 as default"
    CHROME_HOST=172.17.0.1
else
    yellow "using CHROME_HOST=$CHROME_HOST as Ip address to chrome browser"
fi

e2e_params=(--baseUrl "${APP_URL}" --hostname "${CHROME_HOST}" --port 4444 --path "/")

if [[ -z "${SPEC}" ]]; then
    yellow "SPEC not set, will run all"
else
    e2e_params+=(--spec "${SPEC}")
fi

yellow "yarn watch is running, modify code and assets should update automatically."

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

yellow "Starting e2e tests locally..."

createdb e2e-tmp
DB_URL='postgresql:///e2e-tmp' /ella/ops/test/reset_testdata.py --testset e2e
pg_dump e2e-tmp --no-owner >/ella/e2e-test-dump.sql
dropdb e2e-tmp

yellow "Will run tests $SPEC"
DEBUG=true yarn wdio run wdio.conf.js "${e2e_params[@]}"
