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
	# Run migration scripts test
	### Downgrade not supported ###
	# /ella/ella-cli database ci-migration-test -f

	# Run API test on migrated database
	/ella/ella-cli database ci-migration-head -f
	/ella/ella-cli database refresh -f
	py.test --color=yes "/ella/src/api/" -s
else
  /ella/ella-cli database ci-migration-head -f
  /ella/ella-cli database refresh -f
  $@
fi

echo "exits $BASH_SOURCE"


