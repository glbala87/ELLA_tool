#!/bin/bash

# shellcheck disable=SC2034
BLACK=$(tput setaf 0)
RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
# shellcheck disable=SC2034
BLUE=$(tput setaf 4)
MAGENTA=$(tput setaf 5)
# shellcheck disable=SC2034
CYAN=$(tput setaf 6)
# shellcheck disable=SC2034
WHITE=$(tput setaf 7)

# shellcheck disable=SC2034
BOLD=$(tput bold)
RESET=$(tput sgr0)

function green {
    echo -e "${GREEN}$*${RESET}"
}

function magenta {
    echo -e "${MAGENTA}$*${RESET}"
}

function red {
    echo -e "${RED}$*${RESET}"
}
function yellow {
    echo -e "${YELLOW}$*${RESET}"
}

script_dir() {
    local path=$1
    if [[ -z $path ]]; then
        echo "script_dir: path is empty"
        return 1
    fi
    cd "$(dirname "$path")" && pwd -P
}
