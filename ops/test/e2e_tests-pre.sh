#!/bin/bash

# Stuff to do before tests are run:
# - build web assets
# - check if database is ready to receive connections
# - check that we have a folder to put screen shots in

set -e # exit on first failure
source ./scripts/bash-util.sh

/ella/ops/common/symlink_node_modules
yarn production

yellow "Finished building web assets"

#while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

make dbreset

yellow "Now you can start e2e tests"
