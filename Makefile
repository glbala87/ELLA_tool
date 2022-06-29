SHELL = /bin/bash
# Configured on the outside when running in gitlab
BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)
# used as prefix for all containers created in this pipeline. Allows easy cleanup and indentify origin of containers:
UID ?= 1000
GID ?= 1000

PIPELINE_ID ?= ella-${BRANCH}# Configured on the outside when running in gitlab

DEFAULT_CONTAINER_NAME = ella-${BRANCH}
CONTAINER_NAME ?= ella-${BRANCH}
export IMAGE_NAME ?= local/ella-${BRANCH}:latest
REGISTRY_IMAGE = registry.gitlab.com/alleles/ella:${BRANCH}
# use --no-cache to have Docker rebuild the image (using the latests version of all deps)
BUILD_OPTIONS ?=
API_PORT ?= 8000-9999

ELLA_CONFIG ?= /ella/ella-testdata/testdata/example_config.yml
ANNOTATION_SERVICE_URL ?= http://172.17.0.1:6000
ATTACHMENT_STORAGE ?= /ella/ella-testdata/testdata/attachments
TESTSET ?=
HYPOTHESIS_PROFILE ?= 'default'
PGDATA_VOLNAME ?= pgdata-${CONTAINER_NAME}

# e2e test:
PARALLEL_INSTANCES ?= 2

# Diagrams
DIAGRAM_CONTAINER = ${PIPELINE_ID}-diagram
DIAGRAM_IMAGE = local/${PIPELINE_ID}-diagram

TMP_DIR ?= /tmp
ifeq (${CI_REGISTRY_IMAGE},)
# running locally, use interactive
TERM_OPTS := -i -t
else
TERM_OPTS := -t
endif

# override used so docker run defaults can't get clobbered. Use ELLA_OPTS for any customization
override FEATURE_FLAGS = ENABLE_CNV ENABLE_PYDANTIC
override LOCAL_USER = --user ${UID}:${GID}
override ENABLED_FEATURES = $(foreach feat,${FEATURE_FLAGS},-e ${feat}=true)
# use escaped $$PWD so locally generated start_review.sh can be used in the remote VM
override MOUNT_TESTDATA = -v $$PWD/ella-testdata:/ella/ella-testdata -v $$PWD/.git:/ella/.git
override MOUNT_TESTLOG_DIRS = -v $$PWD/errorShots:/ella/errorShots -v $$PWD/logs:/logs

# setup docker options for each variation we use

override SHARED_OPTS = ${ENABLED_FEATURES} \
	${TERM_OPTS} \
	-e ANNOTATION_SERVICE_URL=${ANNOTATION_SERVICE_URL} \
	-e ATTACHMENT_STORAGE=${ATTACHMENT_STORAGE} \
	-e DB_URL=postgresql:///postgres \
	-e ELLA_CONFIG=${ELLA_CONFIG} \
	-e OFFLINE_MODE=false \
	-e REF=${REF} \
	-v ${PGDATA_VOLNAME}:/pg-data \
	--init \
	--name ${CONTAINER_NAME}

override DEV_OPTS = ${SHARED_OPTS} \
	-d \
	-e PTVS_PORT=5678 \
	-p ${API_PORT}:5000 \
	-p 35729:35729 \
	-p 5678:5678 \
	-v ${CURDIR}:/ella \
	--hostname ${CONTAINER_NAME} \
	${ELLA_OPTS}

# pydantic disabled in demo to match production
override DEMO_OPTS = ${MOUNT_TESTDATA} \
	${SHARED_OPTS} \
	-d --rm \
	-e ENABLE_PYDANTIC=false \
	-e PORT=${DEMO_PORT} \
	-e VIRTUAL_HOST=${DEMO_NAME} \
	-p ${DEMO_HOST_PORT}:${DEMO_PORT} \
	-v ${CURDIR}:/local-repo \
	${ELLA_OPTS}

override E2E_BASE_OPTS = ${LOCAL_USER} \
	${MOUNT_TESTDATA} \
	${SHARED_OPTS} \
	-d \
	-e ANNOTATION_SERVICE_URL=http://localhost:6000

override E2E_OPTS = ${E2E_BASE_OPTS} \
	${MOUNT_TESTLOG_DIRS} \
	-e NUM_PROCS=${PARALLEL_INSTANCES} \
	--hostname e2e \
	${ELLA_OPTS}

override E2E_DEBUG_OPTS = ${E2E_BASE_OPTS} \
	-e API_PORT=28752 \
	-e PYTHONIOENCODING=utf-8 \
	-e PYTHONUNBUFFERED=true \
	-p 28752:28752 \
	-p 5859:5859 \
	-v ${CURDIR}:/ella \
	--cap-add SYS_PTRACE \
	--hostname e2e-local \
	${ELLA_OPTS}

override SCHEMA_OPTS = ${LOCAL_USER} \
	${SHARED_OPTS} \
	-v ${CURDIR}:/ella \
	--rm \
	${ELLA_OPTS}

override TEST_OPTS = ${LOCAL_USER} \
	${MOUNT_TESTDATA} \
	${MOUNT_TESTLOG_DIRS} \
	${SHARED_OPTS} \
	--rm \
	${ELLA_OPTS}

.PHONY: help

help :
	@echo
	@echo "-- DEV COMMANDS --"
	@echo
	@echo " Note: The help doc below is derived from value of the git BRANCH/USER/CONTAINER_NAME whose values can be"
	@echo "       set on the command line."
	@echo
	@echo "make build                - build image ${IMAGE_NAME}. Can give docker build options with BUILD_OPTIONS"
	@echo "make dev                  - run image ${IMAGE_NAME}, with container name ${CONTAINER_NAME}"
	@echo "                            Optional: API_PORT, ELLA_OPTS"
	@echo "make db                   - populates the db with fixture data. Use TESTSET variable to choose testset"
	@echo "make url                  - shows the url of your Ella app"
	@echo "make kill                 - stop and remove ${CONTAINER_NAME}"
	@echo "make shell                - get a bash shell into ${CONTAINER_NAME}"
	@echo "make logs                 - tail logs from ${CONTAINER_NAME}"
	@echo "make restart              - restart container ${CONTAINER_NAME}"
	@echo "make any                  - can be prepended to target the first container with pattern ella-.*-${USER}"
	@echo "                            e.g., make any kill"
	@echo
	@echo "-- TEST COMMANDS --"
	@echo "make test-js              - run Javascript tests"
	@echo "make test-common          - run Python tests "
	@echo "make test-api             - run backend API tests"
	@echo "make test-api-migration   - run database migration tests"
	@echo "make test-cli             - run command line interface tests"
	@echo
	@echo "-- END 2 END tests--"
	@echo "make test-e2e             - Run e2e tests"
	@echo "make e2e-test-local       - For running e2e tests locally."
	@echo "                            Requires: APP_URL, CHROME_HOST, SPEC and DEBUG."
	@echo
	@echo "-- DEMO COMMANDS --"
	@echo "make demo-build           - builds the demo image based on the current branch / commit"
	@echo "make demo-build           - pulls the pre-built review Docker image for the current branch from registry.gitlab.com"
	@echo "make demo                 - starts a demo container with testdata at port 3114"
	@echo "make kill-demo            - stops and removes the demo container"
	@echo "make review               - spins up a demo instance on a digitalocean VM with the current branch / commit"
	@echo "                            Set REVIEW_NAME to assign a value to VIRTUAL_HOST"
	@echo
	@echo "-- RELEASE COMMANDS --"
	@echo "make release              - Creates a new Gitlab release with release notes and artifacts from CI"
	@echo "                            Requires: RELEASE_TAG GITLAB_TOKEN"
	@echo "make release-docker       - Build the release Docker image locally and push to registry.gitlab.com"
	@echo "                            Requires: RELEASE_TAG"
	@echo "make release-src          - Bundle backend code, HTML and JS into a local tgz file"
	@echo "                            Requires: RELEASE_TAG, release Docker image built"
	@echo "make release-singularity  - Builds a Singularity image from release Docker image"
	@echo "                            Requires: RELEASE_TAG, release Docker image built"
	@echo "make release-upload       - Uploads the Singularity image and tarball to digitalocean"
	@echo "                            Requires: RELEASE_TAG, awscli installed/configured"
	@echo "make build-singularity    - Builds fresh Docker image locally, then Singularity image"
	@echo "                            Requires: RELEASE_TAG"


# Check that given variables are set and all have non-empty values,
# die with an error otherwise.
#
# From: https://stackoverflow.com/questions/10858261/abort-makefile-if-variable-not-set
#
# Params:
#   1. Variable name(s) to test.
#   2. (optional) Error message to print.
check_defined = \
    $(strip $(foreach 1,$1, \
        $(call __check_defined,$1,$(strip $(value 2)))))
__check_defined = \
    $(if $(value $1),, \
      $(error Undefined $1$(if $2, ($2))))

define sizeof
$$(stat -c %s $1)
endef


#---------------------------------------------
# Production / Releases
#---------------------------------------------

# release settings - general
DIST_DIR ?= dist
DIST_BUILD ?= dist-temp

# release settings - docker
# Normally set in CI, default to IMAGE_NAME for local builds
RELEASE_IMAGE ?= ${IMAGE_NAME}

# release settings - src
STATIC_CONTAINER_NAME = ella-release-static-files
STATIC_BUILD = ${DIST_BUILD}/src/webui/build
API_BUILD = ${DIST_BUILD}/
DIST_BUNDLE = ${DIST_DIR}/ella-release-${RELEASE_TAG}-dist.tgz

# release settings - singularity
SIF_RELEASE ?= ella-release-${RELEASE_TAG}.sif
DIST_SIF = ${DIST_DIR}/${SIF_RELEASE}
SIF_PREFIX ?= docker-daemon

# release settings - upload to digitalocean
RELEASE_BUCKET ?= s3://ella/releases/${RELEASE_TAG}
AWS ?= aws --endpoint https://fra1.digitaloceanspaces.com
AWS_CONFIG_FILE ?= ${HOME}/.aws/config

.PHONY: release build-bundle-image pull-static-image _clean-dist

release:
	$(call check_defined, GITLAB_TOKEN RELEASE_TAG)
	@ops/create_release.py ${GITLAB_TOKEN} ${RELEASE_TAG}

##
## CI release
##

ci-release-docker: _release-build-docker
	docker push ${RELEASE_IMAGE}

ci-release-src: _clean-dist _release-get-static _release-get-api
	tar cz -C ${DIST_BUILD} -f ${DIST_BUNDLE} .
	@echo "Created distribution ${DIST_BUNDLE} ($(call sizeof,${DIST_BUNDLE}) bytes)"

# NOTE: -F overwrites any existing images without prompting, take caution when running locally
ci-release-singularity:
	$(call check_defined, SIF_PREFIX)
	[[ -n ${DIST_DIR} ]] && mkdir -p ${DIST_DIR}
	singularity build -F ${DIST_SIF} ${SIF_PREFIX}://${RELEASE_IMAGE}

ci-release-upload: _ci-release-configure-upload _release-upload-artifacts

##
## Local release
##

release-docker: _release-build-docker
	docker login registry.gitlab.com
	docker push ${RELEASE_IMAGE}

release-src: ci-release-src

release-singularity: ci-release-singularity

# NOTE: assumes awscli installed with valid credentials
release-upload: _release-upload-artifacts

# Builds just the singularity image, no uploading files / docker push
build-singularity: _release-build-docker release-singularity

##
## shared
##

# AWS_CONFIG_FILE is set as a group level CI variable
_ci-release-configure-upload:
	[[ -f ${AWS_CONFIG_FILE} ]] || (echo "No aws config found at ${AWS_CONFIG_FILE}"; exit 1)

_clean-dist:
	$(call check_defined, DIST_BUILD DIST_DIR)
	-rm -rf ${DIST_BUILD}
	mkdir -p ${DIST_DIR} ${DIST_BUILD}

_release-build-docker:
	$(call check_defined, RELEASE_TAG RELEASE_IMAGE)
	# Use git archive to create docker context, to prevent modified files from entering the image.
	git archive --format tar $(if ${CI_COMMIT_SHA},${CI_COMMIT_SHA},${RELEASE_TAG}) | docker build -t ${RELEASE_IMAGE} --target production -

_release-get-api:
	git archive --format tar $(if ${CI_COMMIT_SHA},${CI_COMMIT_SHA},${RELEASE_TAG}) | tar -C ${API_BUILD} -xf -

# Assumes $RELEASE_IMAGE is available locally or can be pulled
_release-get-static:
	-docker rm -vf ${STATIC_CONTAINER_NAME}
	docker run -d \
		--name ${STATIC_CONTAINER_NAME} \
		${RELEASE_IMAGE} \
		sleep infinity
	mkdir -p ${DIST_BUILD}/src/webui
	docker cp ${STATIC_CONTAINER_NAME}:/ella/src/webui/build/ ${STATIC_BUILD}
	docker stop ${STATIC_CONTAINER_NAME}

_release-upload-artifacts:
	ls -l ${DIST_BUNDLE} ${DIST_SIF} || (ls -lA . ${DIST_DIR}; exit 1)
	${AWS} s3 sync --no-progress --acl public-read ${DIST_DIR} ${RELEASE_BUCKET}


#---------------------------------------------
# DEMO / REVIEW APPS
#---------------------------------------------

# demo is a local review app, a review app is a remote demo

.PHONY: review review-stop gitlab-review gitlab-review-stop gitlab-review-refresh-ip review-refresh-ip
.PHONY: demo-build demo-pull demo-check-image demo kill-demo

# set var defaults for running review steps locally
REVAPP_NAME ?= ${BRANCH}
REVAPP_IMAGE_NAME ?= registry.gitlab.com/alleles/ella:${REVAPP_NAME}-review
REVAPP_COMMIT_SHA ?= $(shell git rev-parse HEAD)
export REVAPP_NAME REVAPP_IMAGE_NAME REVAPP_COMMIT_SHA

# set and export demo vars used in ops/start_demo.sh
DEMO_NAME ?= ella-demo
# PORT is the nginx port, not API_PORT
DEMO_PORT ?= 3114
DEMO_HOST_PORT ?= 3114
DEMO_IMAGE ?= ${REVAPP_IMAGE_NAME}
DEMO_USER ?= ${UID}
DEMO_GROUP ?= ${GID}
export DEMO_NAME DEMO_IMAGE DEMO_USER DEMO_GROUP DEMO_PORT DEMO_HOST_PORT

demo-build: build-review

demo-pull:
	docker pull -q ${REVAPP_IMAGE_NAME}

demo-check-image:
	docker image inspect ${REVAPP_IMAGE_NAME} >/dev/null 2>&1 || (echo "you must use demo-build, demo-pull or build ${REVAPP_IMAGE_NAME} yourself"; exit 1)
	-@docker rm -vf ${DEMO_NAME}

demo: demo-check-image
	$(eval export DEMO_IMAGE = ${REVAPP_IMAGE_NAME})
	$(eval CONTAINER_NAME = ${DEMO_NAME})
	docker run ${DEMO_OPTS} ${DEMO_IMAGE}
	docker exec ${TERM_OPTS} ${DEMO_NAME} make dbreset
	@echo "Demo is now running at http://localhost:${DEMO_HOST_PORT}. Some example user/pass are testuser1/demo and testuser5/demo."

kill-demo:
	docker rm -vf ella-demo

# Review apps
define reviewapp-template
docker run -v ${CURDIR}:/local-repo ${ELLA_OPTS} ${REVAPP_IMAGE_NAME} bash -ic "${RUN_CMD} ${RUN_CMD_ARGS}"
endef

__gitlab_env:
	env | grep -E '^(CI|REVAPP|GITLAB|DO_)' > review_env
	echo "PRODUCTION=false" >> review_env
	echo "ENABLE_CNV=true" >> review_env
	$(eval ELLA_OPTS += --env-file=review_env)
	$(eval ELLA_OPTS += -v ${REVAPP_SSH_KEY}:${REVAPP_SSH_KEY})

gitlab-review: __gitlab_env
	$(eval RUN_CMD = make review review-refresh-ip)
	${reviewapp-template}

gitlab-review-stop: __gitlab_env
	$(eval RUN_CMD = make review-stop)
	${reviewapp-template}

gitlab-review-refresh-ip:
	$(eval RUN_CMD = make review-refresh-ip)
	${reviewapp-template}

build-review:
	docker pull -q ${REVAPP_IMAGE_NAME} || true
	docker build ${BUILD_OPTIONS} -t ${REVAPP_IMAGE_NAME} --label commit_sha=${REVAPP_COMMIT_SHA} --target review .

review:
	$(call check_defined, DO_TOKEN, set DO_TOKEN with your DigitalOcean API token and try again)
	$(call check_defined, REVAPP_SSH_KEY, set REVAPP_SSH_KEY with the absolute path to the private ssh key you will use to connect to the remote droplet)
	./ops/review_app.py --token ${DO_TOKEN} create \
		--image-name ${REVAPP_IMAGE_NAME} \
		--ssh-key ${REVAPP_SSH_KEY} \
		--replace \
		${REVAPP_NAME}

review-stop:
	./ops/review_app.py remove ${REVAPP_NAME}

review-refresh-ip:
	$(eval APP_IP = $(shell ./ops/review_app.py status -f ip_address))
	echo APP_IP=${APP_IP} > /local-repo/deploy.env

#---------------------------------------------
# Test data and database
#---------------------------------------------

# see `ops/testdata/fetch-testdata.py --help` for options
FETCH_OPTS ?= --mode https $(if ${CI},--clean,--full)
fetch-testdata:
	python3 ./ops/testdata/fetch-testdata.py $(if ${REF},--ref ${REF},) ${FETCH_OPTS}

ci-fetch-testdata:
	chmod 777 .
	docker run --rm \
		-v ${CURDIR}:/ella \
		${IMAGE_NAME} \
		make fetch-testdata REF="${REF}" FETCH_OPTS="${FETCH_OPTS}"

dbreset: dbsleep
	python3 /ella/ops/testdata/reset-testdata.py $(if ${TESTSET},--testset ${TESTSET},)

dbsleep:
	while ! pg_isready --dbname=postgres --username=postgres; do sleep 5; done

#---------------------------------------------
# DEVELOPMENT
#---------------------------------------------
.PHONY: any build dev url kill shell logs restart db node-inspect create-diagrams
.PHONY: ci-% _in_ci

any:
	$(eval CONTAINER_NAME = $(shell docker ps | awk '/ella-.*-${USER}/ {print $$NF}'))
	@true

build:
	docker build ${BUILD_OPTIONS} -t ${IMAGE_NAME} --target dev .

_in_ci:
	$(call check_defined,CI,aborting ${_ci_stage}: only run CI mode)

# having cache miss every other build, so do an explict pull beforehand even though it "shouldn't"
# be necessary.
# ref: https://github.com/moby/buildkit/issues/1981#issuecomment-1008149971
_ci_pull:
	docker pull -q ${IMAGE_NAME} || docker pull -q ${CI_REGISTRY_IMAGE}:${CI_DEFAULT_BRANCH}

# checking $UPSTREAM_TRIGGER allows the build job to run/pass, so the tests that require the build
# stage can still run. ideally this would be handled by workflow logic, but this works for now.
ifeq (${UPSTREAM_TRIGGER},)
ci-build-dev: override BUILD_OPTIONS += --cache-from ${IMAGE_NAME} --cache-from ${CI_REGISTRY_IMAGE}:${CI_DEFAULT_BRANCH}
ci-build-dev: _ci_stage = build-dev
ci-build-dev: _in_ci _ci_pull build
	$(call check_defined,CI,only push images to registry in CI - aborting $@)
	docker push ${IMAGE_NAME}
	mkdir -p $(dir ${CI_CACHE_IMAGE_FILE})
	docker save ${IMAGE_NAME} >${CI_CACHE_IMAGE_FILE}

ci-build-review: override BUILD_OPTIONS += --cache-from ${REVAPP_IMAGE_NAME} --cache-from ${CI_REGISTRY_IMAGE}:${CI_DEFAULT_BRANCH}-review
ci-build-review: _ci_stage = build-review
ci-build-review: _in_ci build-review
	$(call check_defined,CI,only push images to registry in CI - aborting $@)
	docker push ${REVAPP_IMAGE_NAME}
else
ci-build-%:
	$(info Pipeline triggered by ${UPSTREAM_TRIGGER}, skipping $@)
endif

dev:
	docker run -d ${DEV_OPTS} ${ELLA_OPTS} ${IMAGE_NAME} supervisord -c /ella/ops/dev/supervisor.cfg

db:
	docker exec ${CONTAINER_NAME} make dbreset TESTSET=${TESTSET}

url:
	@./ops/dev/show-url.sh ${CONTAINER_NAME}

kill:
	docker stop ${CONTAINER_NAME}
	docker rm ${CONTAINER_NAME}

shell:
	docker exec -it ${CONTAINER_NAME} bash

logs:
	docker logs -f ${CONTAINER_NAME}

restart:
	docker restart ${CONTAINER_NAME}

# run in docker to use the debugger. optional SPEC_NAME to run a specific spec, otherwise will run all tests
node-inspect:
	node inspect --harmony /dist/node_modules/jest/bin/jest.js --runInBand ${SPEC_NAME}

create-diagrams:
	docker run -v $(shell pwd):/ella ${IMAGE_NAME} python3 /ella/src/vardb/util/datamodel_to_uml.py

update-pipfile:
	docker run \
		-v $(shell pwd):/ella \
		${IMAGE_NAME} \
		pipenv lock

update-yarn:
	docker run \
		-v $(shell pwd):/ella \
		${IMAGE_NAME} \
		yarn install

.PHONY: dump-schemas
dump-schemas:
	docker run ${SCHEMA_OPTS} ${IMAGE_NAME} /ella/scripts/pydantic2ts.sh schemas_${BRANCH}

#---------------------------------------------
# TESTING (unit / modules)
#---------------------------------------------
.PHONY: test-build test-js test-python test-api test-api-migration test-cli test-report test-formatting \
	test-e2e test-e2e-local _run_test _prep_test _run_e2e

# all tests targets below first start a docker container with supervisor as process 1
# and then does an 'exec' of the tests inside the container

test-build:
	docker build ${BUILD_OPTIONS} -t ${IMAGE_NAME} --target dev .

_prep_test:
	$(call check_defined TEST_TYPE)
	$(eval CONTAINER_NAME = ${DEFAULT_CONTAINER_NAME}-${TEST_TYPE})
	-docker rm -vf ${CONTAINER_NAME}
	-docker volume rm ${PGDATA_VOLNAME}
	-docker volume ls | grep pgdata || true
	mkdir -p ${TEST_DIRS}
	chmod a+rwX ${TEST_DIRS}
	@echo

_run_test: TEST_CMD ?= /ella/ops/test/run_${TEST_TYPE}_tests.sh
_run_test: _prep_test
	docker run ${TEST_OPTS} ${SPECIAL_OPTS} ${IMAGE_NAME} ${TEST_CMD}
	docker volume rm ${PGDATA_VOLNAME}

test-js: TEST_TYPE = js
test-js: _run_test

test-python: TEST_TYPE = python
test-python: _run_test

test-api: TEST_TYPE = api
test-api: _run_test

test-api-migration: TEST_TYPE = api-migration
test-api-migration: SPECIAL_OPTS = -e MIGRATION=1
test-api-migration: _run_test

test-cli: TEST_TYPE = cli
test-cli: _run_test

test-report: TEST_TYPE = report
test-report: _run_test

test-formatting: TEST_TYPE = formatting
test-formatting: _run_test

test-testdata: TEST_TYPE = testdata
test-testdata: SPECIAL_OPTS = -e 'TEST_REF=${TEST_REF}'
test-testdata: _run_test

TEST_DIRS = errorShots logs
test-e2e: TEST_TYPE = e2e
test-e2e: _prep_test
	docker run ${E2E_OPTS} ${IMAGE_NAME} supervisord -c /ella/ops/test/supervisor-e2e.cfg
	docker exec -e SPEC=${SPEC} ${TERM_OPTS} ${CONTAINER_NAME} /ella/ops/test/run_e2e_tests.sh || (docker logs ${CONTAINER_NAME} >/ella/logs/docker.log && false)
	docker rm -vf ${CONTAINER_NAME}


#---------------------------------------------
# LOCAL END-2-END TESTING - locally using visible host browser
#                           with webdriverio REPL for debugging
#---------------------------------------------
.PHONY: test-e2e-local

test-e2e-local: TEST_TYPE = e2e-local
test-e2e-local: test-build _prep_test
	docker run ${E2E_DEBUG_OPTS} ${ELLA_OPTS} ${IMAGE_NAME} supervisord -c /ella/ops/test/supervisor-e2e-debug.cfg
	
	CHROME_HOST=$${CHROME_HOST:-$$(docker inspect ${CONTAINER_NAME} --format '{{ .NetworkSettings.Gateway }}')} ; \
	echo using CHROME_HOST=$$CHROME_HOST ; \
	docker exec \
		-e CHROME_HOST=$$CHROME_HOST \
		-e APP_URL=$$APP_URL \
		-e SPEC=$$SPEC \
		-e DEBUG=$$DEBUG \
		-it ${CONTAINER_NAME} \
	    /ella/ops/test/run_e2e_tests_locally.sh
	@echo "remember to 'docker rm ${CONTAINER_NAME}' once you're finished"
