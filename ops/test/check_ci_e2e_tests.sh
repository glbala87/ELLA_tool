#!/bin/bash

set -e # exit on first failure

THISDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"


# Check that all files in src/webui/tests/e2e/tests are in .gitlab-ci.yml
EXIT_CODE=0
for test_path in $THISDIR/../../src/webui/tests/e2e/tests/*.js; do
    test=$(basename ${test_path})

    IN_CI=$(grep "SPEC=${test} make test-e2e" $THISDIR/../../.gitlab-ci.yml) || true
    if [ -z "$IN_CI" ]; then
        echo "${test} is NOT in CI"
        EXIT_CODE=1
    fi
done

if [ $EXIT_CODE == 0 ]; then
    echo "All e2e-tests are in .gitlab-ci.yml"
fi
exit $EXIT_CODE
