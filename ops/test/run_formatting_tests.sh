#!/bin/bash

COLOROFF='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'
LIGHTGREEN='\033[1;32m'

EXIT_CODE=0

# Run black

echo -e "\n${LIGHTGREEN}### Running black ###${COLOROFF}\n"

black --check /ella || EXIT_CODE=1
if [ "$EXIT_CODE" == "1" ]
then
    echo -e "\n${RED}### black: FAILED ###${COLOROFF}\n"
else
    echo -e "\n${GREEN}### black: SUCCESS ###${COLOROFF}\n"
fi

# Run mypy

echo -e "\n${LIGHTGREEN}### Running mypy ###${COLOROFF}\n"

mypy /ella/src/api/main.py || EXIT_CODE=2
if [ "$EXIT_CODE" == "2" ]
then
    echo -e "\n${RED}### mypy: FAILED ###${COLOROFF}\n"
else
    echo -e "\n${GREEN}### mypy: SUCCESS ###${COLOROFF}\n"
fi

# Run prettier

echo -e "\n${LIGHTGREEN}### Running prettier ###${COLOROFF}\n"

# Explicitly run angular parser on html: https://github.com/prettier/prettier-vscode/issues/638#issuecomment-459661114
yarn prettier -l "**/*\.@(js|scss|json|css)" && yarn prettier --parser angular -l "**/*\.@(html)"  || EXIT_CODE=3
if [ "$EXIT_CODE" == "3" ]
then
    echo -e "\n${RED}### prettier: FAILED ###${COLOROFF}\n"
else
    echo -e "\n${GREEN}### prettier: SUCCESS ###${COLOROFF}\n"
fi

exit $EXIT_CODE
