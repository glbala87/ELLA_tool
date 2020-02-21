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
	# Run migration scripts test
	### Downgrade not supported ###
	# ella-cli database ci-migration-test -f

	# Run API test on migrated database
	ella-cli database ci-migration-head -f
	ella-cli database refresh -f
	coverage run -a -m py.test --color=yes --exitfirst "/ella/src/datalayer/" "/ella/src/api/" -s
else
  ella-cli database ci-migration-head -f
  ella-cli database refresh -f
  $@
fi

echo "exits $BASH_SOURCE"
