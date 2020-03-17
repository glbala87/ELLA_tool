#!/bin/bash -ue

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Abort if not migrated
ella-cli database compare

SUPERVISOR_USERNAME=${SUPERVISOR_USERNAME:-ella}
SUPERVISOR_PASSWORD=${SUPERVISOR_USERNAME:-alleles}

SUPERVISOR_CONFIG=${SUPERVISOR_CONFIG:-${DIR}/supervisor.cfg}
envsubst < supervisor-template.cfg | python -c '
import sys
import os
from configparser import ConfigParser
config = ConfigParser(interpolation=None)
config.readfp(sys.stdin)
if not "SUPERVISOR_PORT" in os.environ:
    config.pop("inet_http_server")
for section in config.values():
    [section.pop(k) for k,v in section.items() if not v]

config.write(sys.stdout)
' > ${SUPERVISOR_CONFIG}

export PORT=${PORT:-3114}

# Start services
exec supervisord -c ${SUPERVISOR_CONFIG}
