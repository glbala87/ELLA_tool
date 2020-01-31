#!/bin/bash -ue

THISDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

API_KEY="${1}"
TAG="${2}"

echo "Going to create release using tag ${TAG} on gitlab.com"

echo "Creating release notes..."
release_notes=$("${THISDIR}/create_release_notes.sh" "${TAG}")
released_at=$(git tag -l --format="%(taggerdate:iso8601)" "${TAG}")

echo "Creating payload..."
payload=$(
python - "${TAG}" "${release_notes}" "${released_at}" <<HERE
import sys
import json

tag = sys.argv[1]
release_notes = sys.argv[2]
released_at = sys.argv[3]

print(
    json.dumps({
        "description": release_notes,
        "tag_name": tag,
        "milestones": [tag],
        "released_at": released_at
    })
)
HERE
)

echo "${payload}"



echo "Sending to Gitlab"
curl --fail --header 'Content-Type: application/json' --request POST --data "${payload}" --header "PRIVATE-TOKEN: ${API_KEY}" "https://gitlab.com/api/v4/projects/alleles%2Fella/releases"

echo "Done!"
