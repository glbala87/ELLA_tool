#!/bin/bash

# Wait for DB, export variants and test the output

set -e # exit on first failure
source ./scripts/bash-util.sh

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

yellow "Importing fixtures"
cat /ella/ops/test/report/report-fixture-sample-1.sql | psql postgres

yellow "Testing that Sanger report has variants"

coverage run -a ./src/cli/main.py export sanger --filename e2e-sanger-export testgroup01
# don't include date column in diff (it changes on each test run)
diff <(cut -f2- e2e-sanger-export.csv) <(cut -f2- ops/test/report/sanger-expected.csv) || \
(red "Sanger report (csv) did not have the expected content. Check report/sanger-expected.csv";
 exit 1)

green "[OK]"


yellow "Importing fixtures"
cat /ella/ops/test/report/report-fixture-sample-1-and-2.sql | psql postgres

yellow "Testing that Sanger report is empty when there are no unstarted analyses"

coverage run -a ./src/cli/main.py export sanger --filename e2e-sanger-export testgroup01
grep "file is intentionally empty" e2e-sanger-export.csv || \
	(red "File should could contain a single line with comment; no variants";
    exit 1)

linecount=$(cat e2e-sanger-export.csv | wc -l)
if [ "$linecount" -ne 1 ]
then
	red  "File should could contain a single line with comment; no variants"
    exit 1
fi

green "[OK]"
