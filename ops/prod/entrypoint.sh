#!/bin/bash -ue

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Abort if not migrated
${DIR}/../../ella-cli database compare

export PORT=${PORT:-3114}

# Start services
exec supervisord -c ${DIR}/supervisor.cfg
