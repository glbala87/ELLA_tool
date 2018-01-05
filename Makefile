BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)# Configured on the outside when running in gitlab
# used as prefix for all containers created in this pipeline. Allows easy cleanup and indentify origin of containers:
PIPELINE_ID ?= ella-$(BRANCH)# Configured on the outside when running in gitlab
TEST_NAME ?= all
TEST_COMMAND ?=''
# Container used for local development
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

# Json validation
GP_VALIDATION_CONTAINER = $(PIPELINE_ID)-gp-validation

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
	@echo "make build		- build image $(NAME_OF_GENERATED_IMAGE). use BUILD_OPTIONS variable to set options for 'docker build'"
	@echo "make dev		- run image $(NAME_OF_GENERATED_IMAGE), with container name $(CONTAINER_NAME) :: API_PORT and ELLA_OPTS available as variables"
	@echo "make db			- populates the db with fixture data. Use RESET_DB_SET variable to choose testset (default: small)"
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
	@echo "-- END 2 END tests--"
	@echo "Note! below tests requires 'make e2e-app-container-setup' to be run first"
	@echo "make test-e2e		- Run e2e tests"
	@echo "make test-report-sanger"
	@echo "			- Test report 'ella-cli export sanger'"
	@echo "make test-report-classifications"
	@echo "			- Test report 'ella-cli export classifications'"
	@echo ""
	@echo "make e2e-test-local	- For running e2e tests locally."
	@echo "                          Set these vars: APP_BASE_URL, CHROME_HOST and DEBUG."
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
	    --label io.ousamg.gitversion=$(BRANCH) \
		--name $(CONTAINER_NAME_BUNDLE_STATIC) \
		$(IMAGE_BUNDLE_STATIC) \
		sleep infinity

tar-web-build:
	docker exec -i $(CONTAINER_NAME_BUNDLE_STATIC)  /ella/ops/common/gulp build
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
	docker build -t $(DIAGRAM_IMAGE) -f Dockerfile-diagrams .

start-diagram-container:
	-docker rm $(DIAGRAM_CONTAINER)
	docker run --label io.ousamg.gitversion=$(BRANCH) --name $(DIAGRAM_CONTAINER) -d $(DIAGRAM_IMAGE)  sleep 10s

stop-diagram-container:
	docker stop $(DIAGRAM_CONTAINER)

create-diagram:
	docker exec $(DIAGRAM_CONTAINER) /bin/sh -c 'PYTHONPATH="/ella/src" python datamodel_to_uml.py; dot -Tpng ella-datamodel.dot' > ella-datamodel.png

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
		--label io.ousamg.gitversion=$(BRANCH) \
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
	bash -c "DB_URL='postgresql:///postgres' PYTHONIOENCODING='utf-8' RESET_DB='$(RESET_DB_SET)' python src/api/main.py"

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
	  --label io.ousamg.gitversion=$(BRANCH) \
	  -e ANNOTATION_SERVICE_URL=$(ANNOTATION_SERVICE_URL) \
	  -e ATTACHMENT_STORAGE=$(ATTACHMENT_STORAGE) \
	  -e DB_URL=postgresql:///postgres \
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
	@docker run -d  --name $(GP_VALIDATION_CONTAINER) --label io.ousamg.gitversion=$(BRANCH) $(NAME_OF_GENERATED_IMAGE) sleep infinity
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

test-js: test-build
	docker run -d \
	  --label io.ousamg.gitversion=$(BRANCH) \
	  --name $(PIPELINE_ID)-js \
	  $(NAME_OF_GENERATED_IMAGE) \
	  supervisord -c /ella/ops/common/supervisor.cfg

	docker exec $(PIPELINE_ID)-js /ella/ops/common/gulp unit
	@docker rm -f $(PIPELINE_ID)-js

test-common: test-build
	docker run -d \
	  --label io.ousamg.gitversion=$(BRANCH) \
	  -e DB_URL=postgres:///vardb-test \
	  -e ATTACHMENT_STORAGE=/ella/attachments \
	  --name $(PIPELINE_ID)-common $(NAME_OF_GENERATED_IMAGE) \
	  supervisord -c /ella/ops/test/supervisor.cfg

	docker exec $(PIPELINE_ID)-common ops/test/run_python_tests.sh
	@docker rm -f $(PIPELINE_ID)-common

test-rule-engine: test-build
	docker run -d \
	   --name $(PIPELINE_ID)-rules \
	   --label io.ousamg.gitversion=$(BRANCH) \
	   $(NAME_OF_GENERATED_IMAGE) \
	   supervisord -c /ella/ops/common/supervisor.cfg

	docker exec $(PIPELINE_ID)-rules py.test --color=yes "/ella/src/rule_engine/tests"
	@docker rm -f $(PIPELINE_ID)-rules


test-api: test-build
	docker run -d \
	  --label io.ousamg.gitversion=$(BRANCH) \
	  -e DB_URL=postgres:///vardb-test \
	  -e ATTACHMENT_STORAGE=/ella/attachments \
	  -e ANNOTATION_SERVICE_URL=http://localhost:6000 \
	  --name $(PIPELINE_ID)-api $(NAME_OF_GENERATED_IMAGE) \
	  supervisord -c /ella/ops/test/supervisor.cfg

	docker exec $(PIPELINE_ID)-api ops/test/run_api_tests.sh
	@docker rm -f $(PIPELINE_ID)-api


test-api-migration: test-build
	docker run -d \
	  --label io.ousamg.gitversion=$(BRANCH) \
	  -e DB_URL=postgres:///vardb-test \
	  -e ATTACHMENT_STORAGE=/ella/attachments \
	  -e ANNOTATION_SERVICE_URL=http://localhost:6000 \
	  --name $(PIPELINE_ID)-api-migration $(NAME_OF_GENERATED_IMAGE) \
	  supervisord -c /ella/ops/test/supervisor.cfg

	docker exec $(PIPELINE_ID)-api-migration ops/test/run_api_tests.sh
	@docker rm -f $(PIPELINE_ID)-api-migration


test-cli: test-build # container $(PIPELINE_ID)-cli
	docker run -d \
	  --label io.ousamg.gitversion=$(BRANCH) \
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

e2e-app-container-setup: e2e-network-check e2e-start-chromebox test-build
	-docker stop $(E2E_APP_CONTAINER)
	-docker rm $(E2E_APP_CONTAINER)

	docker run -d \
	   --hostname e2e \
	   --name $(E2E_APP_CONTAINER) \
	   --label io.ousamg.gitversion=$(BRANCH) \
	   -e E2E_APP_CONTAINER=$(E2E_APP_CONTAINER) \
	   --network=local_only --link $(CHROMEBOX_CONTAINER):cb \
	   $(NAME_OF_GENERATED_IMAGE) \
	   supervisord -c /ella/ops/test/supervisor-e2e.cfg

	docker exec $(E2E_APP_CONTAINER) mkdir /ella/errorShots

e2e-app-container-shutdown:
	@echo "Stopping container $(E2E_APP_CONTAINER)"
	docker exec $(E2E_APP_CONTAINER) supervisorctl -c /ella/ops/test/supervisor-e2e.cfg stop web
	docker exec $(E2E_APP_CONTAINER) supervisorctl -c /ella/ops/test/supervisor-e2e.cfg stop postgres
	docker stop $(E2E_APP_CONTAINER)
	docker inspect  --format='{{.Name}}: {{.State.Status}} (exit code: {{.State.ExitCode}})' $(E2E_APP_CONTAINER)


test-e2e: #e2e-app-container-setup # CI run conditional target in separate stage
	docker exec -t $(E2E_APP_CONTAINER) ops/test/run_e2e_tests.sh


e2e-stop-chromebox:
	-docker stop $(CHROMEBOX_CONTAINER)

e2e-remove-chromebox:
	-docker rm $(CHROMEBOX_CONTAINER)

e2e-start-chromebox:
	@echo "Starting Chromebox container $(CHROMEBOX_CONTAINER) using $(CHROMEBOX_IMAGE)"
	docker run -d --name $(CHROMEBOX_CONTAINER) --label io.ousamg.gitversion=$(BRANCH) --network=local_only $(CHROMEBOX_IMAGE)
	@echo "Chromebox info: (chromedriver, chrome, linux, debian)"
	docker exec $(CHROMEBOX_CONTAINER) /bin/sh -c "ps aux | grep -E 'chromedriver|Xvfb' | grep -v 'grep' ; chromedriver --version ; google-chrome --version ; cat /proc/version ; cat /etc/debian_version"

e2e-network-check:
	docker network ls | grep -q local_only || docker network create --subnet 172.25.0.0/16 local_only

#---------------------------------------------
# TESTING of reports (trigged outside container)
#---------------------------------------------
.PHONY: test-report-classifications test-reportsanger

test-report-classifications: #e2e-app-container-setup # CI run conditional target in separate stage
	docker exec -t $(E2E_APP_CONTAINER) ops/test/e2e_tests-pre.sh
	docker exec -t $(E2E_APP_CONTAINER) ops/test/report-classifications/testfixture.sh
	# Create report and run verifications:
	docker exec -t -e DB_URL=postgresql:///postgres $(E2E_APP_CONTAINER) \
	   ops/test/report-classifications/run_tests.sh

test-report-sanger: #e2e-app-container-setup # CI run conditional target in separate stage
	docker exec -t $(E2E_APP_CONTAINER) ops/test/e2e_tests-pre.sh

	docker exec -t $(E2E_APP_CONTAINER) ops/test/report-sanger/testfixture-report-has-variants.sh
	docker exec -t -e DB_URL=postgresql:///postgres $(E2E_APP_CONTAINER) \
	   ops/test/report-sanger/run-test-report-has-variants.sh

	docker exec -t $(E2E_APP_CONTAINER) ops/test/report-sanger/testfixture-report-is-empty.sh
	docker exec -t -e DB_URL=postgresql:///postgres $(E2E_APP_CONTAINER) \
	   ops/test/report-sanger/run-test-report-is-empty.sh


#---------------------------------------------
# LOCAL END-2-END TESTING - locally using visible host browser
#                           with webdriverio REPL for debugging
#---------------------------------------------
.PHONY: e2e-test-local

e2e-test-local: test-build
	-docker rm $(E2E_APP_CONTAINER)
	docker run -d \
	   --name $(E2E_APP_CONTAINER) \
   	   --label io.ousamg.gitversion=$(BRANCH) \
       -it \
       -v $(shell pwd):/ella \
	   -p 5000:5000 -p 5859:5859 \
	   $(NAME_OF_GENERATED_IMAGE) \
	   supervisord -c /ella/ops/test/supervisor-e2e-debug.cfg
	docker exec $(E2E_APP_CONTAINER) make dbsleep
	@docker exec -e CHROME_HOST=$(CHROME_HOST) -e SPECS=$(SPECS) -e DEBUG=$(DEBUG) -it $(E2E_APP_CONTAINER) \
	    /bin/bash -ic "ops/test/run_e2e_tests_locally.sh"



