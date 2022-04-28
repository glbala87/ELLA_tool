#!/bin/bash -ue

# Start API, build web assets and then run e2e tests

# shellcheck disable=1091
source ./scripts/bash-util.sh

yellow "Building web assets"
/ella/ops/common/symlink_node_modules
yarn production
yellow "Finished building web assets"

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

# load e2e dataset, then create a local dump for quicker resets
RESET=/ella/ops/testdata/reset-testdata.py
${RESET} --testset e2e
${RESET} dump --testset e2e

NUM_PROCS=${NUM_PROCS:-2}
yellow "Starting ${NUM_PROCS} parallel e2e tests"

if [[ -z "${SPEC}" ]]; then
    yellow "SPEC not set, will run all"
    SPECS=$(ls src/webui/tests/e2e/tests/*.js)
else
    SPECS=("${SPEC}")
fi

# For live output add --line-buffer to following command
# To exit upon first error, add "--halt now,fail=1"
exec parallel -j "${NUM_PROCS}" -t /ella/ops/test/parallel_e2e_tests_wrapper.sh ::: "${SPECS[@]}"
