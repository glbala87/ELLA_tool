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

if [ "${SPECS}" = "" ]
    then
       yellow "SPECS not set, will run all (or specs mentioned in wdio.conf.js if DEBUG=true is given)"
       # all specs expect the ones used to create test fixtures:
       SPECS=`find  src/webui/tests/e2e/tests -name "*.js" | grep -v "testfixture" | sort | tr "\n" ","`
fi

yellow "Building the application to test"
rm -f /ella/node_modules
ln -s /dist/node_modules/ /ella/node_modules
/ella/node_modules/gulp/bin/gulp.js build

yellow "Finished building web assets with gulp"

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

yellow "Starting e2e tests locally..."

if [ "${DEBUG}" = "" ]
    then
       echo "Will run tests $SPECS"
       /dist/node_modules/webdriverio/bin/wdio \
           --baseUrl "${APP_URL}" --spec ${SPECS} --host "${CHROME_HOST}" --port 4444 --path "/" \
           /ella/src/webui/tests/e2e/wdio.conf.js
    else
        echo "Will run tests $SPECS"
	    DEBUG=true /dist/node_modules/webdriverio/bin/wdio \
           --baseUrl "${APP_URL}" --host "${CHROME_HOST}" --spec ${SPECS} --port 4444 --path "/" \
           /ella/src/webui/tests/e2e/wdio.conf.js
fi


