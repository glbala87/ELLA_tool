#!/bin/bash -ue

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Abort if not migrated
ella-cli database compare

SUPERVISOR_USERNAME=${SUPERVISOR_USERNAME:-ella}
SUPERVISOR_PASSWORD=${SUPERVISOR_USERNAME:-alleles}

# Use supervisor template with envsubst. See template for available environment variables.
# In addition, use python's ConfigParser to remove invalid sections and empty values.
# This is done to provide more functionality of the supervisor config than supervisors
# own environment substitutions.
# Note: Set $SUPERVISOR_CONFIG to a writeable location
SUPERVISOR_CONFIG=${SUPERVISOR_CONFIG:-${DIR}/supervisor.cfg}
envsubst < ${DIR}/supervisor-template.cfg | python -c '
import sys
import os
from configparser import ConfigParser
config = ConfigParser(interpolation=None)
config.read_file(sys.stdin)

# If SUPERVISOR_PORT is not specified, do not include [inet_http_server] in config
if not "SUPERVISOR_PORT" in os.environ:
    config.pop("inet_http_server")

# Remove items where value is empty (equivalent to using supervisor defaults)
for section in config.values():
    [section.pop(k) for k,v in section.items() if not v]

config.write(sys.stdout)
' > ${SUPERVISOR_CONFIG}

export PORT=${PORT:-3114}

# Start services
exec supervisord -c ${SUPERVISOR_CONFIG}
