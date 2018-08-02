#!/bin/bash

# Build web assets and then run e2e tests

set -e # exit on first failure
source ./scripts/bash-util.sh

/ella/ops/common/symlink_node_modules
yarn production

yellow "Finished building web assets"

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

yellow "Starting e2e tests..."

# run all spec expect the ones used to create test fixtures:
find  src/webui/tests/e2e/tests -name "*.js" \
  | grep -v "testfixture" | sort \
  | /dist/node_modules/webdriverio/bin/wdio \
  --baseUrl "${E2E_APP_CONTAINER}:5000" --host "cb" --port 4444 --path "/" \
  /ella/src/webui/tests/e2e/wdio.conf.js
