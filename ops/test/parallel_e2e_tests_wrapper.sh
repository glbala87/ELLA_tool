#!/bin/bash -ue

while ! pg_isready --dbname=postgres --username=postgres; do sleep 2; done

SPEC=${1}

rand_num=$(echo $(( $RANDOM % 35000 + 10000 )))
API_PORT=$rand_num
TAG="e2e-tmp-$rand_num"

echo "Lanching spec $SPEC with tag $TAG"
ATTACHMENT_STORAGE=/ella/attachments/${TAG}
mkdir -p ${ATTACHMENT_STORAGE}

DB_URL=postgresql:///${TAG}
createdb ${TAG}

# Load dump
psql "$DB_URL" < /ella/e2e-test-dump.sql > /dev/null

# Start API
{ DB_URL=$DB_URL API_PORT=$API_PORT ATTACHMENT_STORAGE=$ATTACHMENT_STORAGE SERVE_STATIC=true DEVELOP=true python -u src/api/main.py &> "/logs/api-$TAG"; } &

# Start e2e tests
{ DB_URL=$DB_URL yarn wdio --colors --spec "${SPEC}" --baseUrl "localhost:$API_PORT" --host localhost --port 4444 --path / ; } &

# Wait until either process finishes
wait -n

# Then stop all processes which this process is parent of,
# so we kill the remaining one
pkill -INT -P $$ &> /dev/null
