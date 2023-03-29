#!/bin/bash -e

CURDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
ELLA_URL=https://gitlab.com/alleles/ella.git
ELLA_REPO=$CURDIR/ella
TESTDATA_REPO=$ELLA_REPO/ella-testdata/.git
DEFAULT_ENV_FILE=${CURDIR}/review.env

clone() {
    local repo="$1"
    local dir="$2"
    local args=("--depth=1" "--single-branch" "--recursive")
    if [[ -n "$ELLA_BRANCH" ]]; then
        args+=("--branch" "$ELLA_BRANCH")
    fi
    args+=("$repo" "$dir")
    git clone "${args[@]}"
}

usage() {
    echo
    echo "Clones the alleles/ella repo and starts a demo instance for use as a Gitlab"
    echo "Review app. Assumes existence of env file created by ops/review_app.py."
    echo
    echo "Usage: $(basename "${BASH_SOURCE[0]}") [branch_name]"
    echo
    echo "  branch_name: The name of the branch to review. If not specified, uses the default branch"
    echo
    return 1
}

if (($# > 0)); then
    if [[ "$1" == "--help" || "$1" == "-h" ]]; then
        usage
    fi
    ENV_FILE="$1.env"
else
    ENV_FILE=$DEFAULT_ENV_FILE
fi

# content of env file set in ops/review_app.py:RevappEnviron
if [[ ! -f $ENV_FILE ]]; then
    echo "Could not find env file: $ENV_FILE"
    exit 1
fi
# shellcheck disable=SC1090
source "$ENV_FILE"

if [[ -n $DEBUG ]]; then
    echo "Using env:"
    cat "$ENV_FILE"
    echo
fi

if [[ -d "$ELLA_REPO" ]]; then
    git -C "$ELLA_REPO" pull && git -C "$ELLA_REPO" checkout "$ELLA_BRANCH"
else
    clone "$ELLA_URL" "$ELLA_REPO"
fi

if [[ ! -e "${TESTDATA_REPO}" ]]; then
    echo "Could not find ${TESTDATA_REPO} after cloning ${ELLA_URL}"
    ls -ld ./*/
    exit 1
fi

# start demo container
pushd "${ELLA_REPO}"
make demo-pull demo
