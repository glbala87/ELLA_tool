BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)# Configured on the outside when running in gitlab
PIPELINE_ID ?= ella-$(BRANCH)# Configured on the outside when running in gitlab
TEST_NAME ?= all
TEST_COMMAND ?=''
CONTAINER_NAME ?= $(PIPELINE_ID)
NAME_OF_GENERATED_IMAGE = local/$(PIPELINE_ID)
# use --no-cache to create have Docker rebuild the image (using the latests version of all deps)
BUILD_OPTIONS ?=

API_PORT ?= 8000-9999
ANNOTATION_SERVICE_URL ?= 'http://172.17.0.1:6000'
ATTACHMENT_STORAGE ?= '/ella/attachments/'
RESET_DB_SET ?= 'small'
#RELEASE_TAG =
WEB_BUNDLE=ella-release-$(RELEASE_TAG)-web.tgz
API_BUNDLE=ella-release-$(RELEASE_TAG)-api.tgz
DIST_BUNDLE=ella-release-$(RELEASE_TAG)-dist.tgz

# e2e test:
APP_BASE_URL ?= 'localhost:5000'
CHROME_HOST ?= '172.17.0.1' # maybe not a sensible default
WDIO_OPTIONS ?=  # command line options when running /dist/node_modules/webdriverio/bin/wdio (see 'make wdio')
CHROMEBOX_IMAGE = ousamg/chromebox:1.2
CHROMEBOX_CONTAINER = $(PIPELINE_ID)-chromebox
E2E_APP_CONTAINER = $(PIPELINE_ID)-e2e

# report tests
REPORT_CONTAINER = $(PIPELINE_ID)-report
E2E_TEST_RESULT_IMAGE = local/$(PIPELINE_ID)-e2e-test-result

# Json validation
GP_VALIDATION_CONTAINER = $(PIPELINE_ID)-gp-validation

# distribution
CONTAINER_NAME_BUNDLE_STATIC=ella-web-assets
IMAGE_BUNDLE_STATIC=local/ella-web-assets


.PHONY: help

help :
	@echo ""
	@echo "-- DEV COMMANDS --"
	@echo ""
	@echo " Note! The help doc below is derived from value of the git BRANCH/USER/CONTAINER_NAME whose values can be set on the command line."
	@echo ""
	@echo "make build		- build image $(NAME_OF_GENERATED_IMAGE). use BUILD_OPTIONS variable to set options for 'docker build'"
	@echo "make dev		- run image $(NAME_OF_GENERATED_IMAGE), with container name $(CONTAINER_NAME) :: API_PORT and ELLA_OPTS available as variables"
	@echo "make db			- populates the db with fixture data"
	@echo "make url		- shows the url of your Ella app"
	@echo "make kill		- stop and remove $(CONTAINER_NAME)"
	@echo "make shell		- get a bash shell into $(CONTAINER_NAME)"
	@echo "make logs		- tail logs from $(CONTAINER_NAME)"
	@echo "make restart		- restart container $(CONTAINER_NAME)"
	@echo "make any		- can be prepended to target the first container with pattern ella-.*-$(USER), e.g. make any kill"

	@echo "make check-gp-config    - Validate the genepanel config file set as F=.. argument"
	@echo ""
	@echo "-- TEST COMMANDS --"
	@echo "make test-all		- run all tests"
	@echo "make test-js		- run Javascript tests"
	@echo "make test-common	- run Python tests "
	@echo "make test-api		- run backend API tests"
	@echo "make test-api-migration	- run database migration tests"
	@echo "make test-cli    	- run command line interface tests"
	@echo "                   		Some tests allow you to override the test command by defining TEST_COMMAND=..."
	@echo " 			  	Example: TEST_COMMAND=\"'py.test --exitfirst \"/ella/src/api/util/tests/test_sanger*\" -s'\""
	@echo "make test-e2e		- Run e2e tests"
	@echo "make run-wdio-local	- For running e2e tests locally. Call it inside the shell given by 'make e2e-test-local'."
	@echo "                          Set these vars: APP_BASE_URL and CHROME_HOST"
	@echo "                          WDIO_OPTIONS is also available for setting arbitrary options"

	@echo ""
	@echo "-- DEMO COMMANDS --"
	@echo "make demo		- builds a container to work in tandem with the nginx-proxy container"
	@echo "			  Set DEMO_NAME to assign a value to VIRTUAL_HOST"
	@echo ""

	@echo "-- RELEASE COMMANDS --"
	@echo "make release	        - Noop. See the README.md file"
	@echo "make bundle-static      - Bundle HTML and JS into a local tgz file"
	@echo "make bundle-api         - Bundle the backend code into a local tgz file"


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

.PHONY: release bundle-api bundle-static check-release-tag \
        build-bundle-image start-bundle-container \
        copy-bundle stop-bundle-container

release:
	@echo "See the README.md file, section 'Production'"

bundle-client: check-release-tag build-bundle-image start-bundle-container tar-web-build stop-bundle-container

check-release-tag:
	@$(call check_defined, RELEASE_TAG, 'Missing tag. Please provide a value on the command line')
	git rev-parse --verify "refs/tags/$(RELEASE_TAG)^{tag}"
	git ls-remote --exit-code --tags origin "refs/tags/$(RELEASE_TAG)"

build-bundle-image:
	docker build -t $(IMAGE_BUNDLE_STATIC) .

start-bundle-container:
	-docker stop $(CONTAINER_NAME_BUNDLE_STATIC)
	-docker rm $(CONTAINER_NAME_BUNDLE_STATIC)
	docker run -d \
		--name $(CONTAINER_NAME_BUNDLE_STATIC) \
		$(IMAGE_BUNDLE_STATIC) \
		sleep infinity

tar-web-build:
	docker exec -i $(CONTAINER_NAME_BUNDLE_STATIC)  /ella/ops/common/gulp_build
	docker exec $(CONTAINER_NAME_BUNDLE_STATIC) tar cz -C /ella/src/webui/build -f - . > $(WEB_BUNDLE)
	@echo "Bundled static web files in $(WEB_BUNDLE)"

stop-bundle-container:
	docker stop $(CONTAINER_NAME_BUNDLE_STATIC)

bundle-api: check-release-tag
	git archive -o $(API_BUNDLE) $(RELEASE_TAG)

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
	docker build -t local/ella-diagram -f Dockerfile-diagrams .

start-diagram-container:
	-docker rm ella-diagram-container
	docker run --name ella-diagram-container -d local/ella-diagram  sleep 10s

stop-diagram-container:
	docker stop ella-diagram-container

create-diagram:
	docker exec ella-diagram-container /bin/sh -c 'PYTHONPATH="/ella/src" python datamodel_to_uml.py; dot -Tpng ella-datamodel.dot' > ella-datamodel.png

#---------------------------------------------
# DEMO
#---------------------------------------------

.PHONY: demo dbreset

comma := ,
DEMO_NAME ?= ella-demo

demo:
	docker build -t local/$(DEMO_NAME) .
	-docker stop $(subst $(comma),-,$(DEMO_NAME))
	-docker rm $(subst $(comma),-,$(DEMO_NAME))
	docker run -d \
		--name $(subst $(comma),-,$(DEMO_NAME)) \
		-e VIRTUAL_HOST=$(DEMO_NAME) \
		--expose 80 \
		local/$(DEMO_NAME) \
		supervisord -c /ella/ops/demo/supervisor.cfg
	docker exec $(subst $(comma),-,$(DEMO_NAME)) make dbreset

#---------------------------------------------
# Misc. database
#---------------------------------------------

dbreset: dbsleep dbreset-inner

dbreset-inner:
	bash -c "DB_URL='postgresql:///postgres' PYTHONIOENCODING='utf-8' RESET_DB='small' python src/api/main.py"

dbsleep:
	while ! pg_isready --dbname=postgres --username=postgres; do sleep 5; done

#---------------------------------------------
# DEVELOPMENT
#---------------------------------------------
.PHONY: any build dev url kill shell logs restart db

any:
	$(eval CONTAINER_NAME = $(shell docker ps | awk '/ella-.*-$(USER)/ {print $$NF}'))
	@true

build:
	docker build ${BUILD_OPTIONS} -t $(NAME_OF_GENERATED_IMAGE) .

dev: export USER_CONFIRMATION_ON_STATE_CHANGE="false"
dev: export USER_CONFIRMATION_TO_DISCARD_CHANGES="false"
dev: export OFFLINE_MODE="false"
dev:
	docker run -d \
	--name $(CONTAINER_NAME) \
	--hostname $(CONTAINER_NAME) \
	-e ANNOTATION_SERVICE_URL=$(ANNOTATION_SERVICE_URL) \
	-e ATTACHMENT_STORAGE=$(ATTACHMENT_STORAGE) \
	-p $(API_PORT):5000 \
	$(ELLA_OPTS) \
	-v $(shell pwd):/ella \
	$(NAME_OF_GENERATED_IMAGE) \
	supervisord -c /ella/ops/dev/supervisor.cfg

db:
	docker exec $(CONTAINER_NAME) make dbreset RESET_DB_SET=$(RESET_DB_SET)

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


#---------------------------------------------
# Genepanel config
#---------------------------------------------
.PHONY: check-gp-config

check-gp-config: test-build
	@-docker stop $(GP_VALIDATION_CONTAINER)
	@-docker rm $(GP_VALIDATION_CONTAINER)
	@docker run -d  --name $(GP_VALIDATION_CONTAINER) $(NAME_OF_GENERATED_IMAGE) sleep infinity
	@docker cp $(F) $(GP_VALIDATION_CONTAINER):/tmp/validation-subject
	@docker exec $(GP_VALIDATION_CONTAINER) /bin/bash -c "python ops/dev/check_genepanel_config.py /tmp/validation-subject"
	@echo "Stopping docker container $(GP_VALIDATION_CONTAINER)"
	@docker stop $(GP_VALIDATION_CONTAINER)
	@docker rm $(GP_VALIDATION_CONTAINER)

#---------------------------------------------
# TESTING (unit / modules)
#---------------------------------------------
.PHONY: test-build test test-all test-api test-api-migration \
        test-common test-js test-rule-engine test-cli

# all tests targets below first start a docker container with supervisor as process 1
# and then does an 'exec' of the tests inside the container

test-build:
	docker build ${BUILD_OPTIONS} -t $(NAME_OF_GENERATED_IMAGE) .

test: test-all
test-all: test-js test-common test-api test-cli

test-js: test-build # container $(PIPELINE_ID)-js
	docker run -d --name $(PIPELINE_ID)-js $(NAME_OF_GENERATED_IMAGE) \
	  supervisord -c /ella/ops/common/supervisor.cfg

	docker exec $(PIPELINE_ID)-js /ella/ops/common/gulp unit
	@docker rm -f $(PIPELINE_ID)-js

test-common: test-build # container $(PIPELINE_ID)-common
	docker run -d \
	  -e DB_URL=postgres:///vardb-test \
	  -e ATTACHMENT_STORAGE=/ella/attachments \
	  --name $(PIPELINE_ID)-common $(NAME_OF_GENERATED_IMAGE) \
	  supervisord -c /ella/ops/test/supervisor.cfg

	docker exec $(PIPELINE_ID)-common ops/test/run_python_tests.sh
	@docker rm -f $(PIPELINE_ID)-common

test-rule-engine: test-build # container $(PIPELINE_ID)-rules
	docker run -d --name $(PIPELINE_ID)-rules $(NAME_OF_GENERATED_IMAGE) \
	   supervisord -c /ella/ops/common/supervisor.cfg

	docker exec $(PIPELINE_ID)-rules py.test --color=yes "/ella/src/rule_engine/tests"
	@docker rm -f $(PIPELINE_ID)-rules


test-api: test-build # container $(PIPELINE_ID)-api
	docker run -d \
	  -e DB_URL=postgres:///vardb-test \
	  -e ATTACHMENT_STORAGE=/ella/attachments \
	  -e ANNOTATION_SERVICE_URL=http://localhost:6000 \
	  --name $(PIPELINE_ID)-api $(NAME_OF_GENERATED_IMAGE) \
	  supervisord -c /ella/ops/test/supervisor.cfg

	docker exec $(PIPELINE_ID)-api ops/test/run_api_tests.sh
	@docker rm -f $(PIPELINE_ID)-api


test-api-migration: test-build # container $(PIPELINE_ID)-api-migration
	docker run -d \
	  -e DB_URL=postgres:///vardb-test \
	  -e ATTACHMENT_STORAGE=/ella/attachments \
	  -e ANNOTATION_SERVICE_URL=http://localhost:6000 \
	  --name $(PIPELINE_ID)-api-migration $(NAME_OF_GENERATED_IMAGE) \
	  supervisord -c /ella/ops/test/supervisor.cfg

	docker exec $(PIPELINE_ID)-api-migration ops/test/run_api_tests.sh
	@docker rm -f $(PIPELINE_ID)-api-migration


test-cli: test-build # container $(PIPELINE_ID)-cli
	docker run -d \
	  -e DB_URL=postgres:///vardb-test \
	  -e PANEL_PATH=/ella/src/vardb/testdata/clinicalGenePanels \
	  --name $(PIPELINE_ID)-cli $(NAME_OF_GENERATED_IMAGE) \
	  supervisord -c /ella/ops/test/supervisor.cfg

	docker exec $(PIPELINE_ID)-cli ops/test/run_cli_tests.sh
	@docker rm -f $(PIPELINE_ID)-cli


#---------------------------------------------
# END-2-END TESTING (trigged outside container)
#---------------------------------------------
.PHONY: e2e-log e2e-shell e2e-ps test-e2e \
        e2e-stop-chromebox e2e-start-chromebox e2e-network-check

e2e-log:
	docker logs -f $(E2E_APP_CONTAINER)

e2e-shell:
	docker exec -it $(E2E_APP_CONTAINER) bash

e2e-ps:
	docker exec -it $(E2E_APP_CONTAINER) ps -ejfH

test-e2e: e2e-network-check e2e-start-chromebox test-build
	-docker stop $(E2E_APP_CONTAINER)
	-docker rm $(E2E_APP_CONTAINER)

	@rm -rf errorShots
	@mkdir -p errorShots

	docker run -d --hostname e2e --name $(E2E_APP_CONTAINER) \
	   -v `pwd`/errorShots:/ella/errorShots/  \
	   -e E2E_APP_CONTAINER=$(E2E_APP_CONTAINER) \
	   --network=local_only --link $(CHROMEBOX_CONTAINER):cb \
	   $(NAME_OF_GENERATED_IMAGE) \
	   supervisord -c /ella/ops/test/supervisor-e2e.cfg

	docker exec $(E2E_APP_CONTAINER) ops/test/run_e2e_tests.sh

	docker inspect  --format='{{.Name}}: {{.State.Status}} (exit code: {{.State.ExitCode}})' $(E2E_APP_CONTAINER)

	@echo "Saving testdata from container $(E2E_APP_CONTAINER) to image $(E2E_TEST_RESULT_IMAGE)"
	docker commit  --message "Image with Postgres DB populated through e2e tests" \
	$(E2E_APP_CONTAINER) $(E2E_TEST_RESULT_IMAGE)

	docker stop $(E2E_APP_CONTAINER)
	docker rm $(E2E_APP_CONTAINER)


e2e-remove-report-container:
	-docker stop $(REPORT_CONTAINER)
	-docker rm $(REPORT_CONTAINER)
	-docker rmi $(E2E_TEST_RESULT_IMAGE)

# Export variants from a container whose DB has been populated by running an e2e test.
report-classifications:
	docker run -d --name $(REPORT_CONTAINER) \
	  --hostname report \
	  -v $(shell pwd):/ella \
	  -e PYTHONPATH=/ella/src \
	  -e PGDATA=/data \
	  -e DB_URL=postgresql:///postgres \
	  --entrypoint=""  $(E2E_TEST_RESULT_IMAGE) \
	  supervisord -c /ella/ops/test/supervisor-export.cfg

	docker exec $(REPORT_CONTAINER) ops/test/run_report_classifications_tests.sh

#	@docker stop $(REPORT_CONTAINER)
#	@docker rm $(REPORT_CONTAINER)


e2e-stop-chromebox:
	-docker stop $(CHROMEBOX_CONTAINER)
	-docker rm $(CHROMEBOX_CONTAINER)

e2e-start-chromebox:
	@echo "Starting Chromebox container $(CHROMEBOX_CONTAINER) using $(CHROMEBOX_IMAGE)"
	docker run -d --name $(CHROMEBOX_CONTAINER) --network=local_only $(CHROMEBOX_IMAGE)
	@echo "Chromebox info: (chromedriver, chrome, linux, debian)"
	docker exec $(CHROMEBOX_CONTAINER) /bin/sh -c "ps aux | grep -E 'chromedriver|Xvfb' | grep -v 'grep' ; chromedriver --version ; google-chrome --version ; cat /proc/version ; cat /etc/debian_version"

e2e-network-check:
	docker network ls | grep -q local_only || docker network create --subnet 172.25.0.0/16 local_only

#---------------------------------------------
# LOCAL END-2-END TESTING - locally using visible host browser
#                           with webdriverio REPL for debugging
#---------------------------------------------
.PHONY: e2e-test-local run-wdio-local e2e-start-ella e2e-run-continous e2e-gulp-continous

e2e-test-local: test-build
	-docker rm ella-e2e-local
	docker run --name ella-e2e-local -it -v $(shell pwd):/ella \
	-p 5000:5000 -p 5859:5859 \
	$(NAME_OF_GENERATED_IMAGE) /bin/bash -c "make e2e-run-continous; echo \"Run 'make run-wdio-local' to run e2e tests\"; /bin/bash"

e2e-start-ella:
	supervisord -c /ella/ops/test/supervisor-e2e.cfg
	make dbsleep

e2e-run-continous: e2e-start-ella e2e-gulp-continous

e2e-gulp-continous:
	rm -f /ella/node_modules
	ln -s /dist/node_modules/ /ella/node_modules
        # we want gulp to run continously, watching for file changes:
	supervisorctl -c /ella/ops/test/supervisor-e2e.cfg start gulp

run-wdio-local:
	DEBUG=true /dist/node_modules/webdriverio/bin/wdio $(WDIO_OPTIONS) --baseUrl $(APP_BASE_URL) --host $(CHROME_HOST) --port 4444 --path "/" /ella/src/webui/tests/e2e/wdio.conf.js


