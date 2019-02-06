#!/bin/bash

# Build web assets and then run e2e tests

set -e # exit on first failure
source ./scripts/bash-util.sh

if [ "${APP_URL}" = "" ]
    then
        yellow "Assuming app is running at 127.0.0.1:5000"
        APP_URL="127.0.0.1:5000"
    else
        yellow "Running tests against $APP_URL Ip address to chrome browser"
fi


if [ "${CHROME_HOST}" = "" ]
    then
        yellow "CHROME_HOST not set, using 172.17.0.1 as default"
        CHROME_HOST=172.17.0.1
    else
        yellow "using CHROME_HOST=$CHROME_HOST as Ip address to chrome browser"
fi


if [ "${SPEC}" = "" ]
    then
        yellow "SPEC not set, will run all"
        SPEC_PARAM=""
    else
        SPEC_PARAM="--spec ${SPEC}"
fi

yellow "yarn watch is running, modify code and assets should update automatically."

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

yellow "Starting e2e tests locally..."

rm -f dbdump_e2e.sql

yellow "Will run tests $SPEC"
   DEBUG=true yarn wdio \
   --baseUrl "${APP_URL}" \
   --host "${CHROME_HOST}" \
   --port 4444 --path "/" ${SPEC_PARAM}
