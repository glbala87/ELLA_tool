#!/bin/bash

# Build web assets and then run e2e tests

set -e # exit on first failure

rm -f /ella/node_modules
ln -s /dist/node_modules/ /ella/node_modules
/ella/node_modules/gulp/bin/gulp.js build
echo "Finished building web assets with gulp"

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

echo "Starting e2e tests..."
# screenshots on e2e test errors are defined in wdio.conf
echo "Content of ./errorShots:"
if [ -s './errorShots' ] ; then ls './errorShots' ; else echo "Folder ./errorShots don't exist"; fi
# make sure workflow_sample_classification is run last:
#find  src/webui/tests/e2e/tests -name "*.js" | grep -v "workflow_sample_classification" | sort | /dist/node_modules/webdriverio/bin/wdio --baseUrl "${E2E_APP_CONTAINER}:5000" --host "cb" --port 4444 --path "/" /ella/src/webui/tests/e2e/wdio.conf.js
#find  src/webui/tests/e2e/tests -name "*.js" | grep "workflow_sample_classification" | /dist/node_modules/webdriverio/bin/wdio --baseUrl "${E2E_APP_CONTAINER}:5000" --host "cb" --port 4444 --path "/" /ella/src/webui/tests/e2e/wdio.conf.js
find  src/webui/tests/e2e/tests -name "*.js" | grep "workflow_variant_classification" | /dist/node_modules/webdriverio/bin/wdio --baseUrl "${E2E_APP_CONTAINER}:5000" --host "cb" --port 4444 --path "/" /ella/src/webui/tests/e2e/wdio.conf.js

echo "exits $BASH_SOURCE"