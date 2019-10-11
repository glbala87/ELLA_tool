#!/bin/bash

set -e # exit on first failure

THISDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CI_E2E_TESTS=$(grep -oP "SPEC=\K[^\s]+(?= make test-e2e)" $THISDIR/../../.gitlab-ci.yml | sort)
E2E_TESTS=$(ls src/webui/tests/e2e/tests/ | sort)

if [ "$CI_E2E_TESTS" == "$E2E_TESTS" ]; then
    echo "All E2E tests running in CI"
    exit 0
else
    echo "CI missing E2E tests"
    exit 1
fi
