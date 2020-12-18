#!/bin/bash

set -e # exit on first failure
echo "Starting up postgres"
./ops/common/common_pg_startup init &>/dev/null &
make dbsleep

if [[ "$MIGRATION" == "1" ]]; then
    echo "Will run tests using migrated database"
fi

if [ "$1" = "" ]
then
	py.test --color=yes "/ella/src/datalayer/" "/ella/src/api/" -s
else
  $@
fi

echo "exits $BASH_SOURCE"


