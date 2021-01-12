#!/bin/bash

source ./scripts/bash-util.sh
set -e # exit on first failure

echo "Starting up postgres"
./ops/common/common_pg_startup init &>/dev/null &
make dbsleep

yellow "Starting report tests..."
make dbreset TESTSET=sanger > /dev/null
/ella/ops/test/report/test-report-classifications.sh
