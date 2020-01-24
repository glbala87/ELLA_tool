#!/bin/bash

set -e # exit on first failure

make dbsleep
dropdb --if-exists vardb-test
echo "creating 'vardb-test'"
createdb vardb-test
echo "created 'vardb-test'"

ella-cli database drop -f
ella-cli database make -f

if [ "$1" = "" ]
then
  py.test src --color=yes --ignore src/api --ignore src/cli --ignore src/datalayer
else
  $1
fi

echo "exits $BASH_SOURCE"
