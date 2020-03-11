#!/bin/bash -ue

# Start API, build web assets and then run e2e tests

source ./scripts/bash-util.sh

yellow "Building web assets"
/ella/ops/common/symlink_node_modules
yarn production
yellow "Finished building web assets"

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

yellow "Deposit and create dump of testdata"
createdb e2e-tmp
DB_URL='postgresql:///e2e-tmp' /ella/ops/test/reset_testdata.py --testset e2e
pg_dump e2e-tmp --no-owner > /ella/e2e-test-dump.sql
dropdb e2e-tmp

NUM_PROCS=${NUM_PROCS:-2}
yellow "Starting ${NUM_PROCS} parallel e2e tests"

if [ "${SPEC}" = "" ]
    then
        yellow "SPEC not set, will run all"
        SPECS=$(ls src/webui/tests/e2e/tests/*.js)
    else
        SPECS=($SPEC)
fi

# For live output add --line-buffer to following command
# To exit upon first error, add "--halt now,fail=1"
exec parallel -j "${NUM_PROCS}" -t /ella/ops/test/parallel_e2e_tests_wrapper.sh ::: "${SPECS[@]}"
