#!/bin/bash

BLACK=$(tput setaf 0)
RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
BLUE=$(tput setaf 4)
MAGENTA=$(tput setaf 5)
CYAN=$(tput setaf 6)
WHITE=$(tput setaf 7)

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
