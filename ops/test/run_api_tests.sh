#!/bin/bash

set -e # exit on first failure
echo "Starting up postgres"
./ops/common/common_pg_startup init &>/dev/null &
make dbsleep

if [[ -n "$MIGRATION" ]]; then
    echo "Will run tests using migrated database"
fi

# useful options:
#  -x -- exits on first error
#  -W ignore::DeprecationWarning -- filters out DeprecationWarnings (that we have so damn many of)

pytest_defaults=(--color=yes /ella/src/datalayer /ella/src/api -s)
if [[ -z "$*" ]]; then
    py.test "${pytest_defaults[@]}"
else
    if [[ $(basename -- "$1") == py.test ]]; then
        "$@"
    else
        py.test "${pytest_defaults[@]}" "$@"
    fi
fi

echo "exits ${BASH_SOURCE[0]}"
