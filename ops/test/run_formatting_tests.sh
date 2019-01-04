#!/bin/bash

COLOROFF='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'

EXIT_CODE=0

# Run black

black --check /ella || EXIT_CODE=1
if [ "$EXIT_CODE" == "1" ]
then
    echo -e "${RED}black: FAILED${COLOROFF}"
else
    echo -e "${GREEN}black: SUCCESS${COLOROFF}"
fi

# Run mypy

mypy /ella/src/api/main.py || EXIT_CODE=2
if [ "$EXIT_CODE" == "2" ]
then
    echo -e "${RED}mypy: FAILED${COLOROFF}"
else
    echo -e "${GREEN}mypy: SUCCESS${COLOROFF}"
fi

exit $EXIT_CODE
