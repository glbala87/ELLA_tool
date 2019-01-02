#!/bin/bash

black --check /ella
EXIT_CODE=$?
if [ "$EXIT_CODE" != "0" ]
then
    echo "Code is not correctly formatted with black."
    exit $EXIT_CODE
fi
