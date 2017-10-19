#!/bin/bash

set -e # exit on first failure

# Create release notes using 'git log'

from=$1
to=$2
file=$3 # name of output file

SEP="----------------------"
BLANK_LINE=""

echo "Release notes for E||A" > $file
echo "$SEP" >> $file
echo "Changes from $from to $to" >> $file
echo "$BLANK_LINE" >> $file
git tag --list $from $to --format='%(objecttype) %(refname:strip=2) (%(objectname:short)) "%(contents:subject)" created on %(creatordate:iso-strict) by %(creator)' >> $file
echo "$SEP" >> $file
echo "$BLANK_LINE" >> $file
# Only look at commits from merge requests (not 100%, will also pick up merges into feature branches)
git log --merges "$to..$from" >> $file

