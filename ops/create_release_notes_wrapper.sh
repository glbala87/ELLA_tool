#!/bin/bash
set -e # exit on first failure
# Create release notes based on versions in revisions.txt
LATEST=`cat revisions.txt | grep -v '^[[:space:]]*#' | tr ' ' '\n' | head -n 1`
PREVIOUS=`cat revisions.txt | grep -v '^[[:space:]]*#' | tr ' ' '\n'  | tail -n +2`
# one release notes for each of PREVIOUS[N]..LATEST
echo $PREVIOUS | tr ' ' '\n'  | xargs -I '{}' bash -c "ops/create_release_notes.sh {} ${LATEST} ella-releasenotes_to_${LATEST}_from_{}.txt"