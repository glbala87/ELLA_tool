#!/bin/bash
set -e # exit on first failure

# finalize an analysis. The other unstarted analysis has some variants overlapping with this:
find  src/webui/tests/e2e/tests -name "report_testfixture.js" | /dist/node_modules/webdriverio/bin/wdio --baseUrl "${E2E_APP_CONTAINER}:5000" --host "cb" --port 4444 --path "/" /ella/src/webui/tests/e2e/wdio.conf.js
