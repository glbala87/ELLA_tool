#!/bin/bash

# Wait for DB, export classifications and test the output

set -e # exit on first failure
source ./scripts/bash-util.sh

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

yellow "Importing fixtures"
cat /ella/ops/test/report/report-fixture-sample-1.sql | psql postgres

yellow "Starting test of classifications report..."
coverage run -a ./src/cli/main.py export classifications --filename e2e-variant-export

# Compare only a few fields. Include the report field to test handling html -> text and non-ascii characters:
diff <(cut -f1,2,3,4,12,13,15 e2e-variant-export.csv) <(cut -f1,2,3,4,5,6,7 ops/test/report/classifications-expected.csv) || \
 (red "Content of classification report (csv) wasn't as expected";
  exit 1)

green "[OK]"

yellow "Starting test of classifications report with analysis names..."
coverage run -a ./src/cli/main.py export classifications --filename e2e-variant-export-with-analyses -with_analysis_names

# Compare only a few fields. Include the report field to test handling html -> text and non-ascii characters:
# same verifications as the above with one extra column
diff <(cut -f1,2,3,4,12,13,15,21 e2e-variant-export-with-analyses.csv) <(cut -f1,2,3,4,5,6,7,8 ops/test/report/classifications-expected.csv) || \
 (red "Content of classification report (csv) wasn't as expected";
  exit 1)
green "[OK]"
