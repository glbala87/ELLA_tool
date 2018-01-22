#!/bin/bash -ue

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Abort if not migrated
${DIR}/../../ella-cli database compare

# Refresh shadow tables
echo "Running database refresh (shadow tables etc). This may take a while..."
${DIR}/../../ella-cli database refresh -f

# Start services
supervisord -c ${DIR}/supervisor.cfg
