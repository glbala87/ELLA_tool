#!/bin/bash -e

echo "Starting up postgres"
./ops/common/common_pg_startup init &>/dev/null &
make dbsleep

py.test --color=yes --exitfirst "/ella/src/cli/" -s "$@"

echo "exits ${BASH_SOURCE[0]}"
