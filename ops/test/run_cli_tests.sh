#!/bin/bash

set -e # exit on first failure
echo "Starting up postgres"
./ops/common/common_pg_startup init &>/dev/null &
make dbsleep

if [ "$1" = "" ]
then
	py.test --color=yes --exitfirst "/ella/src/cli/" -s
else
  $@
fi

echo "exits $BASH_SOURCE"
