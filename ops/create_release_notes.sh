#!/bin/bash -ue

TAG="${1}"
git show ${TAG}:docs/releasenotes/README.md | grep "## Highlights" -A 1000000 | sed "s/\.\/img\//https:\/\/gitlab.com\/alleles\/ella\/raw\/${TAG}\/docs\/releasenotes\/img\//g"
