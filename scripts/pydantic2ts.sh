#!/bin/bash -eu
set -o pipefail

# Runs pydantic2json.py and uses that output to generate typescript interfaces
# Optional first arg: set the basename for json/ts output files

log() {
    echo -e "$(date +%Y-%m-%d\ %H:%M:%S) - $*"
}

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

base_output=${1:-master}
json_schemas=$base_output.json
ts_interfaces=$base_output.ts

log "Dumping json schemas to $json_schemas..."
python3 "$DIR/pydantic2json.py" --all --output "$json_schemas"

log "Generating typescript from json schemas..."
npx --package=json-schema-to-typescript -c "json2ts -i $json_schemas" >"$ts_interfaces"
log "Conversion complete!\n"

log "TypeScript interfaces available in $ts_interfaces"
