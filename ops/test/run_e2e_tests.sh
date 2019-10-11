#!/bin/bash

# Start API, build web assets and then run e2e tests

set -e # exit on first failure
source ./scripts/bash-util.sh

mkdir -p /ella/errorShots

if [ "${BUILD}" = "true" ]; then
    yellow "Building web assets"
    /ella/ops/common/symlink_node_modules
    yarn production

    yellow "Finished building web assets"
else
    yellow "Skipping building web assets"
fi

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

yellow "Starting e2e tests..."

if [ "${SPEC}" = "" ]
    then
        yellow "SPEC not set, will run all"
        SPEC_PARAM=""
    else
        SPEC_PARAM="--spec ${SPEC}"
fi


# Run browser e2e
yarn wdio --baseUrl "localhost:5000" --host "localhost" --port 4444 --path "/" ${SPEC_PARAM}
