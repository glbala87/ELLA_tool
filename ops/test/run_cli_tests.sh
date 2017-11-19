#!/bin/bash

set -e # exit on first failure

make dbsleep
dropdb --if-exists vardb-test
echo "creating 'vardb-test'"
createdb vardb-test
echo "created 'vardb-test'"
/ella/ella-cli database drop -f
/ella/ella-cli database make -f

/ella/ella-cli deposit genepanel --folder $PANEL_PATH/HBOC_v01
/ella/ella-cli deposit genepanel --folder $PANEL_PATH/HBOCUTV_v01
/ella/ella-cli users add_groups --name testgroup01 src/vardb/testdata/usergroups.json
/ella/ella-cli users add_many --group testgroup01 src/vardb/testdata/users.json
/ella/ella-cli users list --username testuser1 > cli_output
grep "HBOC_v01" cli_output | grep "HBOCUTV_v01" | grep "testuser1" || \
(echo "Missing genepanels for testuser1. CLI output is:"; cat cli_output; exit 1)

echo "exits $BASH_SOURCE"


