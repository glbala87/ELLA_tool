BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)# Configured on the outside when running in gitlab
# used as prefix for all containers created in this pipeline. Allows easy cleanup and indentify origin of containers:
UID ?= 1000
GID ?= 1000

PIPELINE_ID ?= ella-$(BRANCH)# Configured on the outside when running in gitlab

CONTAINER_NAME ?= ella-$(BRANCH)
export IMAGE_NAME ?= local/ella-$(BRANCH)
# use --no-cache to create have Docker rebuild the image (using the latests version of all deps)
BUILD_OPTIONS ?=
API_PORT ?= 8000-9999

ELLA_CONFIG ?= /ella/example_config.yml
ANNOTATION_SERVICE_URL ?= 'http://172.17.0.1:6000'
ATTACHMENT_STORAGE ?= '/ella/src/vardb/testdata/attachments/'
TESTSET ?= 'default'
HYPOTHESIS_PROFILE ?= 'default'
DIST_DIR ?= dist
WEB_BUNDLE = $(DIST_DIR)/ella-release-$(RELEASE_TAG)-web.tgz
WEB_BUILD = $(DIST_BUILD)/src/webui/build
API_BUNDLE = $(DIST_DIR)/ella-release-$(RELEASE_TAG)-api.tgz
API_BUILD = $(DIST_BUILD)/
DIST_BUNDLE = $(DIST_DIR)/ella-release-$(RELEASE_TAG)-dist.tgz
DIST_BUILD ?= dist-temp
SIF_RELEASE ?= ella-release-$(RELEASE_TAG).sif
SIF_DIST = $(DIST_DIR)/$(SIF_RELEASE)
SIF_PREFIX ?= docker-daemon
RELEASE_BUCKET ?= s3://ella/releases/$(RELEASE_TAG)
AWS ?= aws --endpoint https://fra1.digitaloceanspaces.com
DEFAULT_AWSCLI_CONFIG = $(HOME)/.aws/config
AWSCLI_CONFIG ?= $(DEFAULT_AWSCLI_CONFIG)

# e2e test:
PARALLEL_INSTANCES ?= 2
CHROME_HOST ?= '172.17.0.1' # maybe not a sensible defaults

# Diagrams
DIAGRAM_CONTAINER = $(PIPELINE_ID)-diagram
DIAGRAM_IMAGE = local/$(PIPELINE_ID)-diagram

# distribution
CONTAINER_NAME_BUNDLE_STATIC=$(PIPELINE_ID)-web-assets
IMAGE_BUNDLE_STATIC=local/$(PIPELINE_ID)-web-assets

TMP_DIR ?= /tmp
ifeq ($(CI_REGISTRY_IMAGE),)
# running locally, use interactive
TERM_OPTS := -it
else
TERM_OPTS := -t
endif


.PHONY: help

help :
	@echo
	@echo "-- DEV COMMANDS --"
	@echo
	@echo " Note! The help doc below is derived from value of the git BRANCH/USER/CONTAINER_NAME whose values can be set on the command line."
	@echo
	@echo "make build    - build image $(IMAGE_NAME). use BUILD_OPTIONS variable to set options for 'docker build'"
	@echo "make dev      - run image $(IMAGE_NAME), with container name $(CONTAINER_NAME) :: API_PORT and ELLA_OPTS available as variables"
	@echo "make db       - populates the db with fixture data. Use TESTSET variable to choose testset"
	@echo "make url      - shows the url of your Ella app"
	@echo "make kill     - stop and remove $(CONTAINER_NAME)"
	@echo "make shell    - get a bash shell into $(CONTAINER_NAME)"
	@echo "make logs     - tail logs from $(CONTAINER_NAME)"
	@echo "make restart  - restart container $(CONTAINER_NAME)"
	@echo "make any      - can be prepended to target the first container with pattern ella-.*-$(USER), e.g. make any kill"

	@echo
	@echo "-- TEST COMMANDS --"
	@echo "make test-all            - run all tests"
	@echo "make test-js             - run Javascript tests"
	@echo "make test-common         - run Python tests "
	@echo "make test-api            - run backend API tests"
	@echo "make test-api-migration  - run database migration tests"
	@echo "make test-cli            - run command line interface tests"
	@echo
	@echo "-- END 2 END tests--"
	@echo "make test-e2e        - Run e2e tests"
	@echo "make e2e-test-local  - For running e2e tests locally."
	@echo "                       Set these vars: APP_URL, CHROME_HOST, SPEC and DEBUG."

	@echo
	@echo "-- DEMO COMMANDS --"
	@echo "make demo        - starts a demo container with testdata at port 3114"
	@echo "make kill-demo   - stops and removes the demo container"
	@echo "make review      - builds a container to work in tandem with a nginx-proxy container"
	@echo "                   Set REVIEW_NAME to assign a value to VIRTUAL_HOST"
	@echo

	@echo "-- RELEASE COMMANDS --"
	@echo "make release            - Noop. See the README.md file"
	@echo "make bundle-static      - Bundle HTML and JS into a local tgz file"
	@echo "make bundle-api         - Bundle the backend code into a local tgz file"
	@echo "make build-singularity  - Create release singularity image"


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
$$(stat -c %s $(1))
endef


#---------------------------------------------
# Production / release
#---------------------------------------------

.PHONY: release bundle-api bundle-static \
        build-bundle-image pull-bundle-image \
        clean-dist

release:
	@echo "See the README.md file, section 'Production'"

# CI uses image from gitlab registry, local builds fresh docker / static files
bundle-web: build-bundle-image get-web-bundle
bundle-web-ci: pull-bundle-image get-web-bundle

build-bundle-image:
	docker build -t $(IMAGE_BUNDLE_STATIC) --target production .

pull-bundle-image:
	docker pull $(IMAGE_BUNDLE_STATIC)

get-web-bundle:
	-docker rm -f $(CONTAINER_NAME_BUNDLE_STATIC)
	docker run -d \
		--name $(CONTAINER_NAME_BUNDLE_STATIC) \
		$(IMAGE_BUNDLE_STATIC) \
		sleep infinity
	mkdir -p $(DIST_BUILD)/src/webui
	docker cp $(CONTAINER_NAME_BUNDLE_STATIC):/ella/src/webui/build/ $(WEB_BUILD)
	@echo "Copied static web files to $(WEB_BUILD)"
	docker stop $(CONTAINER_NAME_BUNDLE_STATIC)

bundle-api:
	git archive --format tar $(if $(CI_COMMIT_SHA),$(CI_COMMIT_SHA),$(RELEASE_TAG)) | tar -C $(API_BUILD) -xf -

tar-dist-bundle:
	tar cz -C $(DIST_BUILD) -f $(DIST_BUNDLE) .
	@echo "Created distribution $(DIST_BUNDLE) ($(call sizeof,$(DIST_BUNDLE)) bytes)"

clean-dist:
	$(call check_defined, DIST_BUILD DIST_DIR)
	-rm -rf $(DIST_BUILD)
	mkdir -p $(DIST_DIR) $(DIST_BUILD)

bundle-dist: clean-dist bundle-api bundle-web tar-dist-bundle
bundle-dist-ci: $(eval IMAGE_BUNDLE_STATIC = $(RELEASE_IMAGE))
bundle-dist-ci: clean-dist bundle-api bundle-web-ci tar-dist-bundle

release-notes:
	@ops/create_release_notes_wrapper.sh


#---------------------------------------------
# DEMO / REVIEW APPS
#---------------------------------------------

# demo is a local review app, a review app is a remote demo

.PHONY: review review-stop gitlab-review gitlab-review-stop gitlab-review-refresh-ip review-refresh-ip
.PHONY: demo-build demo-pull demo-check-image demo kill-demo

# set and export demo vars used in ops/start_demo.sh
DEMO_NAME ?= ella-demo
DEMO_PORT ?= 3114
DEMO_HOST_PORT ?= 3114
DEMO_OPTS ?=
DEMO_USER ?= $(UID)
DEMO_GROUP ?= $(shell id -g)
export DEMO_NAME DEMO_PORT DEMO_HOST_PORT DEMO_OPTS DEMO_USER DEMO_GROUP

# set var defaults for running review steps locally
REVAPP_NAME ?= $(BRANCH)
REVAPP_IMAGE_NAME ?= registry.gitlab.com/alleles/ella:$(REVAPP_NAME)-review
REVAPP_COMMIT_SHA ?= $(shell git rev-parse HEAD)
export REVAPP_NAME REVAPP_IMAGE_NAME REVAPP_COMMIT_SHA

demo-build: build-review

demo-pull:
	docker pull $(REVAPP_IMAGE_NAME)

demo-check-image:
	docker image inspect $(REVAPP_IMAGE_NAME) >/dev/null 2>&1 || (echo "you must use demo-build, demo-pull or build $(REVAPP_IMAGE_NAME) yourself"; exit 1)
	-@docker rm -f $(DEMO_NAME)

demo: demo-check-image
	$(eval export DEMO_IMAGE = $(REVAPP_IMAGE_NAME))
	./ops/start_demo.sh
	@echo "Demo is now running at http://localhost:$(DEMO_HOST_PORT). Some example user/pass are testuser1/demo and testuser5/demo."

kill-demo:
	docker rm -f ella-demo

# Review apps
define gitlab-template
docker run --rm $(TERM_OPTS) \
	--user $(UID):$(GID) \
	-v $(shell pwd):/ella \
	-v $(TMP_DIR):/tmp \
	$(ELLA_OPTS) \
	$(REVAPP_IMAGE_NAME) \
	bash -ic "$(RUN_CMD) $(RUN_CMD_ARGS)"
endef

__gitlab_env:
	env | grep -E '^(CI|REVAPP|GITLAB|DO_)' > review_env
	echo "PRODUCTION=false" >> review_env
	$(eval ELLA_OPTS += --env-file=review_env)
	$(eval ELLA_OPTS += -v $(REVAPP_SSH_KEY):$(REVAPP_SSH_KEY))

gitlab-review: __gitlab_env
	$(eval RUN_CMD = make review review-refresh-ip)
	$(gitlab-template)

gitlab-review-stop: __gitlab_env
	$(eval RUN_CMD = make review-stop)
	$(gitlab-template)

gitlab-review-refresh-ip:
	$(eval RUN_CMD = make review-refresh-ip)
	$(gitlab-template)

build-review:
	docker build $(BUILD_OPTIONS) -t $(REVAPP_IMAGE_NAME) --label commit_sha=$(REVAPP_COMMIT_SHA) --target review .

review:
	$(call check_defined, DO_TOKEN, set DO_TOKEN with your DigitalOcean API token and try again)
	$(call check_defined, REVAPP_SSH_KEY, set REVAPP_SSH_KEY with the absolute path to the private ssh key you will use to connect to the remote droplet)
	./ops/review_app.py --token $(DO_TOKEN) create \
		--image-name $(REVAPP_IMAGE_NAME) \
		--ssh-key $(REVAPP_SSH_KEY) \
		$(REVAPP_NAME)

review-stop:
	./ops/review_app.py remove $(REVAPP_NAME)

review-refresh-ip:
	$(eval APP_IP = $(shell ./ops/review_app.py status -f ip_address))
	echo APP_IP=$(APP_IP) > deploy.env

#---------------------------------------------
# Misc. database
#---------------------------------------------

dbreset: dbsleep dbresetinner

dbresetinner:
	@echo "Resetting database"
	DB_URL='postgresql:///postgres' /ella/ops/test/reset_testdata.py --testset $(TESTSET)

dbsleep:
	while ! pg_isready --dbname=postgres --username=postgres; do sleep 5; done

#---------------------------------------------
# DEVELOPMENT
#---------------------------------------------
.PHONY: any build dev url kill shell logs restart db node-inspect create-diagrams

any:
	$(eval CONTAINER_NAME = $(shell docker ps | awk '/ella-.*-$(USER)/ {print $$NF}'))
	@true

build:
	docker build ${BUILD_OPTIONS} -t $(IMAGE_NAME) --target dev .

dev:
	docker run -d \
	  --name $(CONTAINER_NAME) \
	  --hostname $(CONTAINER_NAME) \
	  -e ELLA_CONFIG=$(ELLA_CONFIG) \
	  -e ANNOTATION_SERVICE_URL=$(ANNOTATION_SERVICE_URL) \
	  -e ATTACHMENT_STORAGE=$(ATTACHMENT_STORAGE) \
	  -e OFFLINE_MODE="false" \
	  -e DEV_IGV_FASTA=https://s3.amazonaws.com/igv.broadinstitute.org/genomes/seq/1kg_v37/human_g1k_v37_decoy.fasta \
	  -e DEV_IGV_CYTOBAND=https://s3.amazonaws.com/igv.broadinstitute.org/genomes/seq/b37/b37_cytoband.txt \
	  -e PTVS_PORT=5678 \
	  -e IGV_DATA="/ella/src/vardb/testdata/igv-data/" \
	  -e ANALYSES_PATH="/ella/src/vardb/testdata/analyses/default/" \
	  -e DB_URL=postgresql:///postgres \
	  -e PRODUCTION=false \
	  -p $(API_PORT):5000 \
	  -p 35729:35729 \
	  -p 5678:5678 \
	  $(ELLA_OPTS) \
	  -v $(shell pwd):/ella \
	  $(IMAGE_NAME) \
	  supervisord -c /ella/ops/dev/supervisor.cfg

db:
	docker exec $(CONTAINER_NAME) make dbreset TESTSET=$(TESTSET)

url:
	@./ops/dev/show-url.sh $(CONTAINER_NAME)

kill:
	docker stop $(CONTAINER_NAME)
	docker rm $(CONTAINER_NAME)

shell:
	docker exec -it $(CONTAINER_NAME) bash

logs:
	docker logs -f $(CONTAINER_NAME)

restart:
	docker restart $(CONTAINER_NAME)

# run in docker to use the debugger. optional SPEC_NAME to run a specific spec, otherwise will run all tests
node-inspect:
	node inspect --harmony /dist/node_modules/jest/bin/jest.js --runInBand $(SPEC_NAME)

create-diagrams:
	docker run \
		-v $(shell pwd):/ella \
		-e ELLA_CONFIG=$(ELLA_CONFIG) \
		-e DB_URL=postgresql:///postgres \
		$(IMAGE_NAME) \
		python /ella/src/vardb/util/datamodel_to_uml.py

update-pipfile:
	docker run \
		-v $(shell pwd):/ella \
		$(IMAGE_NAME) \
		pipenv lock


#---------------------------------------------
# TESTING (unit / modules)
#---------------------------------------------
.PHONY: test-build test test-all test-api test-api-migration \
        test-common test-js test-rule-engine test-cli

# all tests targets below first start a docker container with supervisor as process 1
# and then does an 'exec' of the tests inside the container

test-build:
	docker build ${BUILD_OPTIONS} -t $(IMAGE_NAME) --target dev .

test: test-all
test-all: test-js test-common test-api test-cli test-report test-e2e

test-js:
	docker run --rm \
	  --name $(CONTAINER_NAME)-js \
	  --user $(UID):$(GID) \
	  -e PRODUCTION=false \
	  $(IMAGE_NAME) \
	  yarn test

test-js-auto:
	docker run \
	  --name $(CONTAINER_NAME)-js \
	  --user $(UID):$(GID) \
	  -v $(shell pwd):/ella \
	  -e PRODUCTION=false \
	  $(IMAGE_NAME) \
	  yarn test-watch

test-python:
	docker run \
	  $(TERM_OPTS) \
	  --name $(CONTAINER_NAME)-common \
	  --user $(UID):$(GID) \
	  -e ELLA_CONFIG=$(ELLA_CONFIG) \
	  -e PRODUCTION=false \
	  $(IMAGE_NAME) \
	  ops/test/run_python_tests.sh

test-api:
	docker run --rm  \
	  $(TERM_OPTS) \
	  --name $(CONTAINER_NAME)-api \
	  --user $(UID):$(GID) \
	  -e ELLA_CONFIG=$(ELLA_CONFIG) \
	  -e PRODUCTION=false \
	  $(IMAGE_NAME) \
	  /ella/ops/test/run_api_tests.sh


test-api-migration:
	docker run --rm \
	  $(TERM_OPTS) \
	  --name $(CONTAINER_NAME)-api-migration \
	  --user $(UID):$(GID) \
	  -e ELLA_CONFIG=$(ELLA_CONFIG) \
	  -e PRODUCTION=false \
	  -e MIGRATION=1 \
	  $(IMAGE_NAME) \
	  /ella/ops/test/run_api_tests.sh

test-cli:
	docker run --rm \
	  $(TERM_OPTS) \
	  --name $(CONTAINER_NAME)-cli \
	  --user $(UID):$(GID) \
	  -e ELLA_CONFIG=$(ELLA_CONFIG) \
	  -e PRODUCTION=false \
	  $(IMAGE_NAME) \
	  /ella/ops/test/run_cli_tests.sh

test-report:
	docker run --rm \
	  $(TERM_OPTS) \
	  --name $(CONTAINER_NAME)-report \
	  --user $(UID):$(GID) \
	  -e ELLA_CONFIG=$(ELLA_CONFIG) \
	  -e DB_URL=postgresql:///postgres \
	  -e PRODUCTION=false \
	  $(IMAGE_NAME) \
	  ops/test/run_report_tests.sh


test-e2e:
	@-docker rm -f $(CONTAINER_NAME)-e2e
	mkdir -p errorShots
	chmod a+rwX errorShots
	mkdir -p logs
	chmod a+rwX logs
	docker run -d --hostname e2e \
	   --name $(CONTAINER_NAME)-e2e \
	   --user $(UID):$(GID) \
	   -v $(shell pwd)/errorShots:/ella/errorShots \
	   -v $(shell pwd)/logs:/logs \
	   -e ELLA_CONFIG=$(ELLA_CONFIG) \
	   -e ANALYSES_PATH=/ella/src/vardb/testdata/analyses/e2e/ \
	   -e NUM_PROCS=$(PARALLEL_INSTANCES) \
	   -e DEV_IGV_FASTA=https://s3.amazonaws.com/igv.broadinstitute.org/genomes/seq/1kg_v37/human_g1k_v37_decoy.fasta \
	   -e DEV_IGV_CYTOBAND=https://s3.amazonaws.com/igv.broadinstitute.org/genomes/seq/b37/b37_cytoband.txt \
	   -e PRODUCTION=false \
	   -e ANNOTATION_SERVICE_URL=http://localhost:6000 \
	   -e DB_URL=postgresql:///postgres \
	   $(IMAGE_NAME) \
	   supervisord -c /ella/ops/test/supervisor-e2e.cfg

	docker exec -e SPEC=$(SPEC) -t $(CONTAINER_NAME)-e2e ops/test/run_e2e_tests.sh
	@docker rm -f $(CONTAINER_NAME)-e2e

test-formatting:
	docker run --rm \
	  $(TERM_OPTS) \
	  --name $(CONTAINER_NAME)-formatting \
	  --user $(UID):$(GID) \
	  $(IMAGE_NAME) \
	  ops/test/run_formatting_tests.sh

#---------------------------------------------
# LOCAL END-2-END TESTING - locally using visible host browser
#                           with webdriverio REPL for debugging
#---------------------------------------------
.PHONY: e2e-test-local

e2e-test-local: test-build
	-docker rm -f $(CONTAINER_NAME)-e2e-local
	docker run -d \
	   --name $(CONTAINER_NAME)-e2e-local \
	   --user $(UID):$(GID) \
       -it \
       -v $(shell pwd):/ella \
	   -e ELLA_CONFIG=$(ELLA_CONFIG) \
	   -e ANALYSES_PATH=/ella/src/vardb/testdata/analyses/e2e/ \
	   -e PRODUCTION=false \
	   -e DB_URL=postgresql:///postgres \
	   -e DEV_IGV_FASTA=https://s3.amazonaws.com/igv.broadinstitute.org/genomes/seq/1kg_v37/human_g1k_v37_decoy.fasta \
	   -e DEV_IGV_CYTOBAND=https://s3.amazonaws.com/igv.broadinstitute.org/genomes/seq/b37/b37_cytoband.txt \
	   -e API_PORT=28752 \
	   -e ANNOTATION_SERVICE_URL=http://localhost:6000 \
	   -p 28752:28752 -p 5859:5859 \
	   $(IMAGE_NAME) \
	   supervisord -c /ella/ops/test/supervisor-e2e-debug.cfg
	@docker exec -e CHROME_HOST=$(CHROME_HOST) -e APP_URL=$(APP_URL) -e SPEC=$(SPEC) -e DEBUG=$(DEBUG) -it $(CONTAINER_NAME)-e2e-local \
	    /bin/bash -ic "ops/test/run_e2e_tests_locally.sh"

#---------------------------------------------
# CI Releases and Building Singularity images
#---------------------------------------------
.PHONY: _release-build-docker ci-release-upload

ci-release-docker: _release-build-docker
	docker push $(RELEASE_IMAGE)

ci-release-src: bundle-dist-ci

ci-release-singularity: _release-build-sif

ci-release-upload: _release-configure-upload
	ls -l $(DIST_BUNDLE) $(SIF_DIST) || (ls -lA . $(DIST_DIR); exit 1)
	# mv $(SIF_DIST) $(DIST_DIR)/
	# ls -lA $(DIST_DIR)
	$(AWS) s3 sync --no-progress --acl public-read $(DIST_DIR) $(RELEASE_BUCKET)

_release-build-docker:
	$(call check_defined, RELEASE_TAG RELEASE_IMAGE)
	# Use git archive to create docker context, to prevent modified files from entering the image.
	git archive --format tar $(if $(CI_COMMIT_SHA),$(CI_COMMIT_SHA),$(RELEASE_TAG)) | docker build -t $(RELEASE_IMAGE) --target production -

_release-build-sif:
	$(call check_defined, SIF_PREFIX)
	[ -n $(DIST_DIR) ] && mkdir -p $(DIST_DIR)
	# NOTE: -F overwrites any existing images without prompting, take caution when running locally
	singularity build -F $(SIF_DIST) $(SIF_PREFIX)://$(RELEASE_IMAGE)

_release-configure-upload:
	[ -f $(AWSCLI_CONFIG) ] || (echo "No aws config found at $(AWSCLI_CONFIG)"; exit 1)
	mkdir -p $(HOME)/.aws
	[ -f $(DEFAULT_AWSCLI_CONFIG) ] || cp $(AWSCLI_CONFIG) $(DEFAULT_AWSCLI_CONFIG)

# build release sif locally
build-singularity: _release-build-docker _release-build-sif
