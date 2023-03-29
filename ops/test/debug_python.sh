#!/bin/bash -e
shopt -s inherit_errexit

for fname in ops/test/run_{api,python}_tests.sh; do
    ./$fname -x -W ignore::DeprecationWarning
done

./ops/test/run_formatting_tests.sh
./scripts/pydantic2json.py --all >/dev/null
