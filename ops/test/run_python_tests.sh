#!/bin/bash

set -e # exit on first failure
echo "Starting up postgres"
./ops/common/common_pg_startup init &>/dev/null &
make dbsleep

pytest_defaults=(src --color=yes --ignore src/api --ignore src/cli --ignore src/datalayer -s)
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
