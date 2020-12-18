#!/bin/bash

pushd /ella
source ./scripts/bash-util.sh

EXIT_CODE=0

function run() {
    name=$1
    cmd=$2
    magenta "### Running ${name} ###"
    /bin/bash -c "$cmd"
    if [ "$?" != "0" ]
    then
        EXIT_CODE=1
        red "### ${name}: FAILED ###"
    else
        green "### ${name}: SUCCESS ###"
    fi
}

run "black" "black --check /ella"
run "mypy" "mypy /ella/src/api/main.py"
run "flake8" "flake8"
run "prettier" "yarn prettier -l '**/*\.@(js|scss|json|css|html|yml)'"
run "eslint" "yarn eslint /ella"
exit $EXIT_CODE
