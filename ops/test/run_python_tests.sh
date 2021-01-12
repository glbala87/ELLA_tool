#!/bin/bash

set -e # exit on first failure
echo "Starting up postgres"
./ops/common/common_pg_startup init &>/dev/null &
make dbsleep

if [ "$1" = "" ]
then
  py.test src --color=yes --ignore src/api --ignore src/cli --ignore src/datalayer -s
else
  $1
fi

echo "exits $BASH_SOURCE"
