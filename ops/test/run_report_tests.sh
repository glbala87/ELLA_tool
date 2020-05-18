#!/bin/bash

set -e # exit on first failure
source ./scripts/bash-util.sh

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

yellow "Starting report tests..."
make dbreset TESTSET=sanger > /dev/null
/ella/ops/test/report/test-report-classifications.sh
