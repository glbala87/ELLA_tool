#!/bin/bash

# Wait for DB, export variants and test the output

set -e # exit on first failure

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done
echo "Starting report tests..."
./ella-cli export sanger --filename e2e-sanger-export
grep "file is intentionally empty" e2e-sanger-export.csv
linecount = $(wc -l e2e-sanger-export.csv)
if [ "$linecount" -ne 1 ]
then
	echo "File should have single line"; exit 1)
fi

echo "exits $BASH_SOURCE"