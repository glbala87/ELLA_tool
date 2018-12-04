#!/bin/bash -ue

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Abort if not migrated
${DIR}/../../ella-cli database compare

# Start services
supervisord -c ${DIR}/supervisor.cfg
