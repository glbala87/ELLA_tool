#!/bin/bash

# Wait for DB, export variants and test the output

set -e # exit on first failure
source ./scripts/bash-util.sh

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

yellow "Testing that Sanger report has variants"

./ella-cli export sanger --filename e2e-sanger-export
diff e2e-sanger-export.csv ops/test/report-sanger/expected.csv || \
(red "Sanger report (csv) did have the expected content";
 exit 1)

green "[OK]"