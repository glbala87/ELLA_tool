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
       # all specs expect the ones used to create test fixtures:
       SPEC=`find  src/webui/tests/e2e/tests -name "*.js" | grep -v "testfixture" | sort | tr "\n" "," | sed 's/,$//g'`
fi

yellow "Building the application to test"
/ella/ops/common/symlink_node_modules
yarn production

yellow "Finished building web assets"

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

yellow "Starting e2e tests locally..."

yellow "Will run tests $SPEC"
   DEBUG=${DEBUG}  yarn wdio \
   --baseUrl "${APP_URL}" \
   --spec ${SPEC} \
   --host "${CHROME_HOST}" \
   --port 4444 --path "/"
