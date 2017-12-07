#!/bin/bash

# Wait for DB, export variants and test the output

set -e # exit on first failure
source ./scripts/bash-util.sh

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

yellow "Testing that Sanger report is empty when there are no unstarted analyses"

./ella-cli export sanger --filename e2e-sanger-export
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
