#!/bin/bash

set -e # exit on first failure

make dbsleep
dropdb --if-exists vardb-test
echo "creating 'vardb-test'"
createdb vardb-test
echo "created 'vardb-test'"

/ella/ella-cli database drop -f
/ella/ella-cli database make -f

if [ "$1" = "" ]
then
  py.test src -k 'not test_ui' --color=yes --cov src --cov-report xml --ignore src/api
else
  $1
fi

echo "exits $BASH_SOURCE"