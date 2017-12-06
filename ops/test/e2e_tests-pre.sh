#!/bin/bash

# Stuff to do before tests are run:
# - build web assets
# - check if database is ready to receive connections
# - check that we have a folder to put screen shots in

set -e # exit on first failure

rm -f /ella/node_modules
ln -s /dist/node_modules/ /ella/node_modules
/ella/node_modules/gulp/bin/gulp.js build
echo "Finished building web assets with gulp"

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

# screenshots on e2e test errors are defined in wdio.conf
echo "Content of ./errorShots:"
if [ -s './errorShots' ] ; then ls './errorShots' ; else echo "Folder ./errorShots don't exist"; fi
echo "Now you can start e2e tests"
