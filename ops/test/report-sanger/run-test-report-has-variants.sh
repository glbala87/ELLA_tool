#!/bin/bash

# Wait for DB, export variants and test the output

set -e # exit on first failure
source ./scripts/bash-util.sh

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

yellow "Testing that Sanger report has variants"

./ella-cli export sanger --filename e2e-sanger-export
# don't include date column in diff (it changes on each test run)
diff <(cut -f2- e2e-sanger-export.csv) <(cut -f2- ops/test/report-sanger/expected.csv) || \
(red "Sanger report (csv) did not have the expected content. Check report-sanger/expected.csv";
 exit 1)

green "[OK]"