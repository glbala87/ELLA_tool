#!/bin/bash

# Build web assets and then run e2e tests

set -e # exit on first failure
source ./scripts/bash-util.sh

if [ -z ${CHROME_HOST+x}]
    then 
        echo "CHROME_HOST not set, using 172.17.0.1 as default"
        export CHROME_HOST=172.17.0.1
    else
        echo "using CHROME_HOST=$CHROME_HOST as Ip address to chrome browser"
fi

rm -f /ella/node_modules
ln -s /dist/node_modules/ /ella/node_modules
/ella/node_modules/gulp/bin/gulp.js build

yellow "Finished building web assets with gulp"

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

yellow "Starting e2e tests locally..."

# run all spec expect the ones used to create test fixtures:
find  src/webui/tests/e2e/tests -name "*.js" \
  | grep -v "testfixture" | sort \
  | DEBUG=true /dist/node_modules/webdriverio/bin/wdio \
  --baseUrl "127.0.0.1:5000" --host "${CHROME_HOST}" --port 4444 --path "/" \
  /ella/src/webui/tests/e2e/wdio.conf.js
