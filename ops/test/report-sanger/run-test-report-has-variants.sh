#!/bin/bash

# Wait for DB, export variants and test the output

set -e # exit on first failure

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done
echo "Starting report tests..."
./ella-cli export sanger --filename e2e-sanger-export
diff e2e-sanger-export.csv ops/test/report-sanger/expected.csv

echo "exits $BASH_SOURCE"