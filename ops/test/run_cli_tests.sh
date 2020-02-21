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
	coverage run -a -m py.test --color=yes --exitfirst "/ella/src/cli/" -s
else
  $@
fi

echo "exits $BASH_SOURCE"
