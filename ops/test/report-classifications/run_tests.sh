#!/bin/bash

# Wait for DB, export classifications and test the output

set -e # exit on first failure

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done
echo "Starting report tests..."
./ella-cli export classifications --filename e2e-variant-export
# Compare only a few fields. Include the report field to test handling html -> text and non-ascii characters:
diff <(cut -f1,2,3,4,13 e2e-variant-export.csv) <(cut -f1,2,3,4,5 ops/test/report-classifications/expected.csv )

echo "exits $BASH_SOURCE"