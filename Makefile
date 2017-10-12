BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)# Configured on the outside when running in gitlab
TEST_NAME ?= all
TEST_COMMAND ?=''
CONTAINER_NAME ?= ella-$(BRANCH)-$(USER)
NAME_OF_GENERATED_IMAGE = local/ella-$(BRANCH)
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
CHROMEBOX_CONTAINER = chromebox-$(BRANCH)

.PHONY: help

help :
	@echo ""
	@echo "-- DEV COMMANDS --"
	@echo ""
	@echo " Note! The help doc below is derived from value of the git BRANCH/USER/CONTAINER_NAME whose values can be set on the command line."
	@echo ""
	@echo "make build		- build image $(NAME_OF_GENERATED_IMAGE)"
	@echo "make dev		- run image $(NAME_OF_GENERATED_IMAGE), with container name $(CONTAINER_NAME) :: API_PORT and ELLA_OPTS available as variables"
	@echo "make db			- populates the db with fixture data"
	@echo "make url		- shows the url of your Ella app"
	@echo "make kill		- stop and remove $(CONTAINER_NAME)"
	@echo "make shell		- get a bash shell into $(CONTAINER_NAME)"
	@echo "make logs		- tail logs from $(CONTAINER_NAME)"
	@echo "make restart		- restart container $(CONTAINER_NAME)"
	@echo "make any		- can be prepended to target the first container with pattern ella-.*-$(USER), e.g. make any kill"
	@echo ""
	@echo "-- TEST COMMANDS --"
	@echo "make test		- build image local/ella-test, then run all tests"
	@echo "make single-test	- build image local/ella-test :: TEST_NAME={api | common | js | cli | api-migration} required as variable or will default to 'all'"
	@echo "                          optional variable TEST_COMMAND=... will override the py.test command"
	@echo " 			  Example: TEST_COMMAND=\"'py.test --exitfirst \"/ella/src/api/util/tests/test_sanger*\" -s'\""
	@echo "make e2e-test		- build image local/ella-test, then run e2e tests"
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

.PHONY: release bundle-api bundle-static check-release-tag build-bundle-image start-bundle-container copy-bundle stop-bundle-container

CONTAINER_NAME_BUNDLE_STATIC=ella-web-assets
IMAGE_BUNDLE_STATIC=local/ella-web-assets

release:
	@echo "See the README.md file, section 'Production'"

bundle-client: check-release-tag build-bundle-image start-bundle-container tar-web-build stop-bundle-container

check-release-tag:
	@$(call check_defined, RELEASE_TAG, 'Missing tag. Please provide a value on the command line')
#	git rev-parse --verify "refs/tags/$(RELEASE_TAG)^{tag}" in git >= 1.8.5, tomato is stuck on 1.8.3.1
	git rev-parse --verify "refs/tags/$(RELEASE_TAG)^{commit}"
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

.PHONY: diagrams build-diagram-image start-diagram-container create-diagram stop-diagram-container

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

dbreset: dbsleep dbreset-inner

dbreset-inner:
	bash -c "DB_URL='postgresql:///postgres' PYTHONIOENCODING='utf-8' RESET_DB='small' python src/api/main.py"

dbsleep:
	while ! pg_isready; do sleep 5; done


#---------------------------------------------
# DEVELOPMENT
#---------------------------------------------
.PHONY: any build dev url kill shell logs restart db

any:
	$(eval CONTAINER_NAME = $(shell docker ps | awk '/ella-.*-$(USER)/ {print $$NF}'))
	@true

build:
	docker build -t $(NAME_OF_GENERATED_IMAGE) .

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
	-p 35729:35729 \
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
# TESTING
#---------------------------------------------
.PHONY: test-build test single-test e2e-test e2e-test-local run-wdio-local run-wdio-against-chromebox run-test

test-build:
	docker build -t $(NAME_OF_GENERATED_IMAGE) .

test: test-build run-test

single-test: test-build run-test

e2e-test: e2e-network-check e2e-start-chromebox test-build
	-docker stop ella-e2e
	-docker rm ella-e2e
	@rm -rf errorShots
	@mkdir -p errorShots
	docker run -v `pwd`/errorShots:/ella/errorShots/ --name ella-e2e --network=local_only --link $(CHROMEBOX_CONTAINER):cb $(NAME_OF_GENERATED_IMAGE) make e2e-start-ella-and-run-wdio
	make e2e-stop-chromebox


e2e-test-local: test-build
	-docker rm ella-e2e-local
	docker run --name ella-e2e-local -it -v $(shell pwd):/ella -p 5000:5000 -p 5859:5859 $(NAME_OF_GENERATED_IMAGE) /bin/bash -c "make e2e-run-continous; echo \"Run 'make run-wdio-local' to run e2e tests\"; /bin/bash"

run-test:
	docker run $(NAME_OF_GENERATED_IMAGE) make test-$(TEST_NAME) TEST_COMMAND=$(TEST_COMMAND)

e2e-start-ella:
	supervisord -c /ella/ops/test/supervisor-e2e.cfg
	make dbsleep

e2e-start-ella-and-run-wdio: e2e-start-ella e2e-gulp-once run-wdio-against-chromebox

e2e-run-continous: e2e-start-ella e2e-gulp-continous

e2e-gulp-continous:
	rm -f /ella/node_modules
	ln -s /dist/node_modules/ /ella/node_modules
        # we want gulp to run continously, watching for file changes:
	supervisorctl -c /ella/ops/test/supervisor-e2e.cfg start gulp

e2e-gulp-once:
	rm -f /ella/node_modules
	ln -s /dist/node_modules/ /ella/node_modules
	/ella/node_modules/gulp/bin/gulp.js build

run-wdio-against-chromebox:
	echo CHROMEBOX_CONTAINER = $(CHROMEBOX_CONTAINER)
	echo BRANCH = $(BRANCH)
# $(CHROMEBOX_CONTAINER) is 'chromebox_', seems the BRANCH isn't set properly in this task
	@echo "Running webdriverio against chromebox in container $(CHROMEBOX_CONTAINER). Running if responds: `curl --silent cb:4444/status`"
	@echo "pwd: '`pwd`'"
#	screenshots on e2e test errors are defined in wdio.conf
	@echo "Content of ./errorShots:"
	@if [ -s './errorShots' ] ; then ls './errorShots' ; else echo "Folder ./errorShots don't exist"; fi
	/dist/node_modules/webdriverio/bin/wdio --baseUrl "ella-e2e:5000" --host "cb" --port 4444 --path "/" /ella/src/webui/tests/e2e/wdio.conf.js

run-wdio-local:
	DEBUG=true /dist/node_modules/webdriverio/bin/wdio $(WDIO_OPTIONS) --baseUrl $(APP_BASE_URL) --host $(CHROME_HOST) --port 4444 --path "/" /ella/src/webui/tests/e2e/wdio.conf.js

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
# TESTING - INSIDE CONTAINER ONLY
#---------------------------------------------
.PHONY: test-all test-api test-api-migration test-common test-js test-cli test-e2e

test-all: test-js test-common test-api test-cli

test-api: export PGDATABASE=vardb-test
test-api: export DB_URL=postgres:///vardb-test
test-api: export PYTHONPATH=/ella/src
test-api: export ANNOTATION_SERVICE_URL=http://localhost:6000
test-api: export ATTACHMENT_STORAGE=/ella/attachments
test-api:
	supervisord -c /ella/ops/test/supervisor.cfg
	make dbsleep
	dropdb --if-exists vardb-test
	createdb vardb-test
	/ella/ella-cli database drop -f
	/ella/ella-cli database make -f
ifeq ($(TEST_COMMAND),) # empty?
	py.test --color=yes "/ella/src/api/" -s
else
	$(TEST_COMMAND)
endif

test-api-migration: export PGDATABASE=vardb-test
test-api-migration: export DB_URL=postgres:///vardb-test
test-api-migration: export PYTHONPATH=/ella/src
test-api-migration: export ANNOTATION_SERVICE_URL=http://localhost:6000
test-api-migration: export ATTACHMENT_STORAGE=/ella/attachments
test-api-migration:
	supervisord -c /ella/ops/test/supervisor.cfg
	make dbsleep
	dropdb --if-exists vardb-test
	createdb vardb-test
ifeq ($(TEST_COMMAND),) # empty?
	# Run migration scripts test
	/ella/ella-cli database ci-migration-test -f

	# Run API test on migrated database
	/ella/ella-cli database ci-migration-head -f
	py.test --color=yes "/ella/src/api/" -s
else
	$(TEST_COMMAND)
endif

test-rule-engine: export PYTHONPATH=/ella/src
test-rule-engine:
	py.test --color=yes "/ella/src/rule_engine/tests"

test-common: export PGDATABASE=vardb-test
test-common: export DB_URL=postgres:///vardb-test
test-common: export PYTHONPATH=/ella/src
test-common: export ATTACHMENT_STORAGE=/ella/attachments
test-common:
	supervisord -c /ella/ops/test/supervisor.cfg
	make dbsleep
	dropdb --if-exists vardb-test
	createdb vardb-test
	/ella/ella-cli database drop -f
	/ella/ella-cli database make -f
ifeq ($(TEST_COMMAND),) # empty?
	py.test src -k 'not test_ui' --color=yes --cov src --cov-report xml --ignore src/api
else
	$(TEST_COMMAND)
endif

test-js:
	@rm -f /ella/node_modules
	@ln -s /dist/node_modules/ /ella/node_modules
	/ella/node_modules/gulp/bin/gulp.js unit


test-cli: export PGDATABASE=vardb-test
test-cli: export DB_URL=postgres:///vardb-test
test-cli: export PYTHONPATH=/ella/src
test-cli: export PANEL_PATH=/ella/src/vardb/testdata/clinicalGenePanels
test-cli:
	supervisord -c /ella/ops/test/supervisor.cfg
	@make dbsleep
	@dropdb --if-exists vardb-test
	@createdb vardb-test
	@/ella/ella-cli database drop -f
	@/ella/ella-cli database make -f
	/ella/ella-cli deposit genepanel --folder $(PANEL_PATH)/HBOC_v01
	/ella/ella-cli deposit genepanel --folder $(PANEL_PATH)/HBOCUTV_v01
	/ella/ella-cli users add_groups --name testgroup01 src/vardb/testdata/usergroups.json
	/ella/ella-cli users add_many --group testgroup01 src/vardb/testdata/users.json
	/ella/ella-cli users list --username testuser1 > cli_output
	@grep "HBOC_v01" cli_output | grep "HBOCUTV_v01" | grep "testuser1" || \
(echo "Missing genepanels for testuser1. CLI output is:"; cat cli_output; exit 1)
