BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)# Configured on the outside when running in gitlab
# used as prefix for all containers created in this pipeline. Allows easy cleanup and indentify origin of containers:
UID ?= 1000
GID ?= 1000

PIPELINE_ID ?= ella-$(BRANCH)# Configured on the outside when running in gitlab

CONTAINER_NAME ?= ella-$(BRANCH)
IMAGE_NAME ?= local/ella-$(BRANCH)
# use --no-cache to create have Docker rebuild the image (using the latests version of all deps)
BUILD_OPTIONS ?=

API_PORT ?= 8000-9999
ANNOTATION_SERVICE_URL ?= 'http://172.17.0.1:6000'
ATTACHMENT_STORAGE ?= '/ella/attachments/'
TESTSET ?= 'default'
HYPOTHESIS_PROFILE ?= 'default'
#RELEASE_TAG =
WEB_BUNDLE=ella-release-$(RELEASE_TAG)-web.tgz
API_BUNDLE=ella-release-$(RELEASE_TAG)-api.tgz
DIST_BUNDLE=ella-release-$(RELEASE_TAG)-dist.tgz

# e2e test:
CHROME_HOST ?= '172.17.0.1' # maybe not a sensible defaults

# Diagrams
DIAGRAM_CONTAINER = $(PIPELINE_ID)-diagram
DIAGRAM_IMAGE = local/$(PIPELINE_ID)-diagram

# distribution
CONTAINER_NAME_BUNDLE_STATIC=$(PIPELINE_ID)-web-assets
IMAGE_BUNDLE_STATIC=local/$(PIPELINE_ID)-web-assets


.PHONY: help

help :
	@echo ""
	@echo "-- DEV COMMANDS --"
	@echo ""
	@echo " Note! The help doc below is derived from value of the git BRANCH/USER/CONTAINER_NAME whose values can be set on the command line."
	@echo ""
	@echo "make build		- build image $(IMAGE_NAME). use BUILD_OPTIONS variable to set options for 'docker build'"
	@echo "make dev		- run image $(IMAGE_NAME), with container name $(CONTAINER_NAME) :: API_PORT and ELLA_OPTS available as variables"
	@echo "make db			- populates the db with fixture data. Use TESTSET variable to choose testset"
	@echo "make url		- shows the url of your Ella app"
	@echo "make kill		- stop and remove $(CONTAINER_NAME)"
	@echo "make shell		- get a bash shell into $(CONTAINER_NAME)"
	@echo "make logs		- tail logs from $(CONTAINER_NAME)"
	@echo "make restart	- restart container $(CONTAINER_NAME)"
	@echo "make any		- can be prepended to target the first container with pattern ella-.*-$(USER), e.g. make any kill"

	@echo ""
	@echo "-- TEST COMMANDS --"
	@echo "make test-all		- run all tests"
	@echo "make test-js		- run Javascript tests"
	@echo "make test-common	- run Python tests "
	@echo "make test-api		- run backend API tests"
	@echo "make test-api-migration	- run database migration tests"
	@echo "make test-cli    	- run command line interface tests"

	@echo "-- END 2 END tests--"
	@echo "make test-e2e		- Run e2e tests"
	@echo "make e2e-test-local	- For running e2e tests locally."
	@echo "                          Set these vars: APP_URL, CHROME_HOST, SPEC and DEBUG."

	@echo ""
	@echo "-- DEMO COMMANDS --"
	@echo "make demo		- starts a demo container with testdata at port 3114"
	@echo "make kill-demo	- stops and removes the demo container"
	@echo "make review		- builds a container to work in tandem with a nginx-proxy container"
	@echo "			      Set REVIEW_NAME to assign a value to VIRTUAL_HOST"
	@echo ""

	@echo "-- RELEASE COMMANDS --"
	@echo "make release	           - Noop. See the README.md file"
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

#---------------------------------------------
# Production / release
#---------------------------------------------

.PHONY: release bundle-api bundle-static \
        build-bundle-image start-bundle-container \
        stop-bundle-container

release:
	@echo "See the README.md file, section 'Production'"

bundle-client: build-bundle-image start-bundle-container tar-web-build stop-bundle-container

build-bundle-image:
	docker build -t $(IMAGE_BUNDLE_STATIC) --target dev .

start-bundle-container:
	-docker stop $(CONTAINER_NAME_BUNDLE_STATIC)
	-docker rm $(CONTAINER_NAME_BUNDLE_STATIC)
	docker run -d \
		--name $(CONTAINER_NAME_BUNDLE_STATIC) \
		$(IMAGE_BUNDLE_STATIC) \
		sleep infinity

tar-web-build:
	docker exec -i $(CONTAINER_NAME_BUNDLE_STATIC)  yarn build
	docker exec -i $(CONTAINER_NAME_BUNDLE_STATIC)  yarn docs
	docker exec $(CONTAINER_NAME_BUNDLE_STATIC) tar cz -C /ella/src/webui/build -f - . > $(WEB_BUNDLE)
	@echo "Bundled static web files in $(WEB_BUNDLE)"

stop-bundle-container:
	docker stop $(CONTAINER_NAME_BUNDLE_STATIC)

bundle-api: REF=$(if $(CI_COMMIT_SHA),$(CI_COMMIT_SHA),$(RELEASE_TAG))
bundle-api:
	git archive -o $(API_BUNDLE) $(REF)

bundle-dist: bundle-api bundle-client
	@rm -rf dist-temp
	mkdir -p dist-temp/src/webui/build
	tar x -C dist-temp/src/webui/build -f $(WEB_BUNDLE)
	tar x -C dist-temp -f $(API_BUNDLE)
	tar cz -C dist-temp -f $(DIST_BUNDLE) .
	@echo "Created distribution $(DIST_BUNDLE) ($(shell du -k $(DIST_BUNDLE) | cut -f1))"
	@rm -rf dist-temp

release-notes:
	@ops/create_release_notes_wrapper.sh

#---------------------------------------------
# Create diagram of the datamodel
#---------------------------------------------

.PHONY: diagrams build-diagram-image start-diagram-container \
        create-diagram stop-diagram-container

diagrams: build-diagram-image start-diagram-container create-diagram stop-diagram-container

build-diagram-image:
	docker build -t $(DIAGRAM_IMAGE) -f Dockerfile-diagrams .

start-diagram-container:
	-docker rm $(DIAGRAM_CONTAINER)
	docker run --name $(DIAGRAM_CONTAINER) -d $(DIAGRAM_IMAGE)  sleep 10s

stop-diagram-container:
	docker stop $(DIAGRAM_CONTAINER)

create-diagram:
	docker exec $(DIAGRAM_CONTAINER) /bin/sh -c 'PYTHONPATH="/ella/src" python datamodel_to_uml.py; dot -Tpng ella-datamodel.dot' > ella-datamodel.png

#---------------------------------------------
# DEMO / REVIEW APPS
#---------------------------------------------

.PHONY: demo kill-demo review

comma := ,
REVIEW_NAME ?=
REVIEW_OPTS ?=

# Demo is just a review app, with port mapped to system
demo: REVIEW_OPTS=-p 3114:3114
demo: REVIEW_NAME=demo
demo: review
demo:
	@echo "Demo is now running at http://localhost:3114. Some example user/pass are testuser1/demo and testuser5/demo."

kill-demo:
	docker rm -f ella-demo

# Review apps
review:
	$(call check_defined, REVIEW_NAME)
	docker build -t local/ella-$(REVIEW_NAME) --target dev .
	-docker stop $(subst $(comma),-,ella-$(REVIEW_NAME))
	-docker rm $(subst $(comma),-,ella-$(REVIEW_NAME))
	docker run -d \
		--name $(subst $(comma),-,ella-$(REVIEW_NAME)) \
		--user $(UID):$(GID) \
		-e PRODUCTION=false \
		-e VIRTUAL_HOST=$(REVIEW_NAME) \
		-e PORT=3114 \
		--expose 3114 \
		$(REVIEW_OPTS) \
		local/ella-$(REVIEW_NAME) \
		supervisord -c /ella/ops/demo/supervisor.cfg
	docker exec $(subst $(comma),-,ella-$(REVIEW_NAME)) make dbreset

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
.PHONY: any build dev url kill shell logs restart db node-inspect

any:
	$(eval CONTAINER_NAME = $(shell docker ps | awk '/ella-.*-$(USER)/ {print $$NF}'))
	@true

build:
	docker build ${BUILD_OPTIONS} -t $(IMAGE_NAME) --target dev .

dev: export USER_CONFIRMATION_ON_STATE_CHANGE="false"
dev: export USER_CONFIRMATION_TO_DISCARD_CHANGES="false"
dev: export OFFLINE_MODE="false"
dev:
	docker run -d \
	  --name $(CONTAINER_NAME) \
	  --hostname $(CONTAINER_NAME) \
	  -e ANNOTATION_SERVICE_URL=$(ANNOTATION_SERVICE_URL) \
	  -e ATTACHMENT_STORAGE=$(ATTACHMENT_STORAGE) \
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
	docker run \
	  --rm \
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
	docker run -d \
	  --name $(CONTAINER_NAME)-common \
	  --user $(UID):$(GID) \
	  -e DB_URL=postgresql:///vardb-test \
	  -e ATTACHMENT_STORAGE=/ella/attachments \
	  -e PRODUCTION=false \
	  -e HYPOTHESIS_PROFILE=$(HYPOTHESIS_PROFILE) \
	  $(IMAGE_NAME) \
	  supervisord -c /ella/ops/test/supervisor.cfg

	docker exec $(CONTAINER_NAME)-common ops/test/run_python_tests.sh
	@docker rm -f $(CONTAINER_NAME)-common

test-api:
	docker run -d \
	  --name $(CONTAINER_NAME)-api \
	  --user $(UID):$(GID) \
	  -e DB_URL=postgresql:///vardb-test \
	  -e ATTACHMENT_STORAGE=/ella/attachments \
	  -e PRODUCTION=false \
	  -e ANNOTATION_SERVICE_URL=http://localhost:6000 \
	  -e HYPOTHESIS_PROFILE=$(HYPOTHESIS_PROFILE) \
	  $(IMAGE_NAME) \
	  supervisord -c /ella/ops/test/supervisor.cfg

	docker exec $(CONTAINER_NAME)-api ops/test/run_api_tests.sh
	@docker rm -f $(CONTAINER_NAME)-api

test-api-migration:
	docker run -d \
	  --name $(CONTAINER_NAME)-api-migration \
	  --user $(UID):$(GID) \
	  -e DB_URL=postgresql:///vardb-test \
	  -e ATTACHMENT_STORAGE=/ella/attachments \
	  -e PRODUCTION=false \
	  -e ANNOTATION_SERVICE_URL=http://localhost:6000 \
	  $(IMAGE_NAME) \
	  supervisord -c /ella/ops/test/supervisor.cfg

	docker exec $(CONTAINER_NAME)-api-migration ops/test/run_api_migration_tests.sh
	@docker rm -f $(CONTAINER_NAME)-api-migration

test-cli:
	docker run -d \
	  --name $(CONTAINER_NAME)-cli \
	  --user $(UID):$(GID) \
	  -e DB_URL=postgresql:///vardb-test \
	  -e TESTDATA=/ella/src/vardb/testdata/ \
	  -e PRODUCTION=false \
	  $(IMAGE_NAME) \
	  supervisord -c /ella/ops/test/supervisor.cfg

	docker exec $(CONTAINER_NAME)-cli ops/test/run_cli_tests.sh
	@docker rm -f $(CONTAINER_NAME)-cli

test-report:
	docker run -d \
	  --name $(CONTAINER_NAME)-report \
	  --user $(UID):$(GID) \
	  -e DB_URL=postgresql:///postgres \
	  -e PRODUCTION=false \
	  $(IMAGE_NAME) \
	  supervisord -c /ella/ops/test/supervisor.cfg

	docker exec -t $(CONTAINER_NAME)-report ops/test/run_report_tests.sh
	@docker rm -f $(CONTAINER_NAME)-report

test-e2e:
	@-docker rm -f $(CONTAINER_NAME)-e2e
	mkdir -p errorShots
	docker run -d --hostname e2e \
	   --name $(CONTAINER_NAME)-e2e \
	   --user $(UID):$(GID) \
	   -v $(shell pwd)/errorShots:/ella/errorShots \
	   -e BUILD=$(BUILD) \
	   -e PRODUCTION=false \
	   -e ANNOTATION_SERVICE_URL=http://localhost:6000 \
	   -e DB_URL=postgresql:///postgres \
	   $(IMAGE_NAME) \
	   supervisord -c /ella/ops/test/supervisor-e2e.cfg

	docker exec -e SPEC=$(SPEC) -t $(CONTAINER_NAME)-e2e ops/test/run_e2e_tests.sh
	@docker rm -f $(CONTAINER_NAME)-e2e

test-check-ci-e2e-tests:
	docker run --rm \
	  --name $(CONTAINER_NAME)-formatting \
	  --user $(UID):$(GID) \
	  $(IMAGE_NAME) \
	  ops/test/check_ci_e2e_tests.sh

test-formatting:
	docker run --rm \
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
	   -e PRODUCTION=false \
	   -e DB_URL=postgresql:///postgres \
	   -e ANNOTATION_SERVICE_URL=http://localhost:6000 \
	   -p 5000:5000 -p 5859:5859 \
	   $(IMAGE_NAME) \
	   supervisord -c /ella/ops/test/supervisor-e2e-debug.cfg
	@docker exec -e CHROME_HOST=$(CHROME_HOST) -e APP_URL=$(APP_URL) -e SPEC=$(SPEC) -e DEBUG=$(DEBUG) -it $(CONTAINER_NAME)-e2e-local \
	    /bin/bash -ic "ops/test/run_e2e_tests_locally.sh"

build-singularity:
	$(call check_defined, RELEASE_TAG)
	# Use git archive to create docker context, to prevent modified files from entering the image.
	git archive --format tar.gz $(RELEASE_TAG) | docker build -t local/ella-singularity-build --target production -
	@-docker rm -f ella-tmp-registry
	docker run --rm -d -p 29000:5000 --name ella-tmp-registry registry:2
	docker tag local/ella-singularity-build localhost:29000/local/ella-singularity-build
	docker push localhost:29000/local/ella-singularity-build
	@-rm -f ella-release-$(RELEASE_TAG).simg
	SINGULARITY_NOHTTPS=1 singularity build ella-release-$(RELEASE_TAG).simg docker://localhost:29000/local/ella-singularity-build
	docker rm -f ella-tmp-registry
