#!/bin/bash

# Stuff to do before tests are run:
# - build web assets
# - check if database is ready to receive connections
# - check that we have a folder to put screen shots in

set -e # exit on first failure
source ./scripts/bash-util.sh

rm -f /ella/node_modules
ln -s /dist/node_modules/ /ella/node_modules
/ella/node_modules/gulp/bin/gulp.js build

yellow "Finished building web assets with gulp"

#while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

make dbreset

yellow "Now you can start e2e tests"
