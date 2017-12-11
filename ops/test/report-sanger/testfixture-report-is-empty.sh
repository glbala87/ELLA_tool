#!/bin/bash
set -e # exit on first failure

# finalize the second analysis giving no unstarted analyses
find  src/webui/tests/e2e/tests -name "report_testfixture_b.js" | /dist/node_modules/webdriverio/bin/wdio --baseUrl "${E2E_APP_CONTAINER}:5000" --host "cb" --port 4444 --path "/" /ella/src/webui/tests/e2e/wdio.conf.js
