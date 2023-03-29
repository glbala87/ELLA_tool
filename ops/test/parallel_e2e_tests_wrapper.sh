#!/bin/bash -ue

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

SPEC=$1

rand_num=$((RANDOM % 35000 + 10000))
API_PORT=$rand_num
TAG="e2e-tmp-$rand_num"

echo "Lanching spec $SPEC with tag $TAG"
ATTACHMENT_STORAGE=/ella/attachments/${TAG}
mkdir -p "${ATTACHMENT_STORAGE}"

export DB_URL=postgresql:///${TAG}
createdb ${TAG}

# Load dump
/ella/ops/testdata/reset-testdata.py --testset e2e

# Start API
{ DB_URL=$DB_URL API_PORT=$API_PORT ATTACHMENT_STORAGE=$ATTACHMENT_STORAGE DEVELOP=true python -u src/api/main.py &>"/logs/api-$TAG.log"; } &

# Start e2e tests
{ DB_URL=$DB_URL yarn wdio --colors --spec "${SPEC}" --baseUrl "localhost:$API_PORT" --host localhost --port 4444 --path /; } &

# Wait until either process finishes
wait -n

# Then stop all processes which this process is parent of,
# so we kill the remaining one
pkill -INT -P $$ &>/dev/null
