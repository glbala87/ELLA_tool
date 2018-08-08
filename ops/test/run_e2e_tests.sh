#!/bin/bash

# Start API, build web assets and then run e2e tests

set -e # exit on first failure
source ./scripts/bash-util.sh

mkdir /ella/errorShots

yellow "Starting API"
supervisord -c /ella/ops/test/supervisor-e2e.cfg

yellow "Building web assets"
/ella/ops/common/symlink_node_modules
yarn production

yellow "Finished building web assets"

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

yellow "Starting e2e tests..."

# Run browser e2e
yarn wdio --baseUrl "${E2E_APP_CONTAINER}:5000" --host "cb" --port 4444 --path "/"


yellow "Starting report tests..."
make dbreset TESTSET=sanger
/ella/ops/test/report/test-report-classifications.sh
/ella/ops/test/report/test-report-sanger.sh
