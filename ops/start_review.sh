#!/bin/bash -e

if [[ ! -d ella-testdata ]]; then
    git clone https://gitlab.com/alleles/ella-testdata.git --depth=1
fi
mkdir -p .git
