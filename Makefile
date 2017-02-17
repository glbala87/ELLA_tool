BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)
TEST_NAME ?= all
TEST_COMMAND ?=''
CONTAINER_NAME ?= ella-$(BRANCH)-$(USER)
IMAGE_NAME = local/ella-$(BRANCH)
API_PORT ?= 8000-9999
RESET_DB_SET ?= 'small'

# e2e test:
APP_BASE_URL ?= 'localhost:5000'
CHROME_HOST ?= '172.17.0.1' # maybe not a sensible default
WDIO_OPTIONS ?=  # command line options when running /dist/node_modules/webdriverio/bin/wdio (see 'make wdio')

.PHONY: help

help :
	@echo ""
	@echo "-- DEV COMMANDS --"
	@echo "make build		- build image $(IMAGE_NAME)"
	@echo "make dev		- run image $(IMAGE_NAME), with container name $(CONTAINER_NAME) :: API_PORT and ELLA_OPTS available as variables"
	@echo "make db		- populates the db with fixture data"
	@echo "make url		- shows the url of your Ella app"
	@echo "make kill		- stop and remove $(CONTAINER_NAME)"
	@echo "make shell		- get a bash shell into $(CONTAINER_NAME)"
	@echo "make logs		- tail logs from $(CONTAINER_NAME)"
	@echo "make restart		- restart container $(CONTAINER_NAME)"
	@echo "make any		- can be prepended to target the first container with pattern ella-.*-$(USER), e.g. make any kill"
	@echo ""
	@echo "-- TEST COMMANDS --"
	@echo "make test		- build image local/ella-test, then run all tests"
	@echo "make single-test	- build image local/ella-test :: TEST_NAME={api | common | js | api-migration} required as variable or will default to 'all'"
	@echo "                          optional variable TEST_COMMAND=... will override the py.test command"
	@echo " 			  Example: TEST_COMMAND=\"'py.test --exitfirst \"/ella/src/api/util/tests/test_sanger*\" -s'\""
	@echo "make e2e-test		- build image local/ella-test, then run e2e tests"
	@echo "make wdio		- For running e2e tests locally. Call it inside the shell given by 'make e2e-test-local'."
	@echo "                          Set these vars: APP_BASE_URL and CHROME_HOST"
	@echo "                          WDIO_OPTIONS is also available for setting arbitrary options"

	@echo ""
	@echo "-- RELEASE COMMANDS --"
	@echo "make core		- builds a core (development) image named ousamg/ella-core"
	@echo "make release		- builds a production image named ousamg/ella-release"

#---------------------------------------------
# DEMO
#---------------------------------------------

.PHONY: demo dbreset

comma := ,
DEMO_NAME ?= none

demo:
	-docker build -t local/$(DEMO_NAME) .
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
.PHONY: any build dev fancy-dev url kill shell logs restart db

any:
	$(eval CONTAINER_NAME = $(shell docker ps | awk '/ella-.*-$(USER)/ {print $$NF}'))
	@true

build:
	docker build -t $(IMAGE_NAME) .

dev: export USER_CONFIRMATION_ON_STATE_CHANGE="false"
dev: export USER_CONFIRMATION_TO_DISCARD_CHANGES="false"
dev:
	docker run -d \
	--name $(CONTAINER_NAME) \
	-p $(API_PORT):5000 \
	$(ELLA_OPTS) \
	-v $(shell pwd):/ella \
	$(IMAGE_NAME) \
	supervisord -c /ella/ops/dev/supervisor.cfg

fancy-dev:
	sed -i 's poll //poll ' gulpfile.js
	$(MAKE) dev
	$(MAKE) db
	git checkout gulpfile.js

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
.PHONY: test-build test single-test e2e-test e2e-test-local wdio wdio-chromebox run-test

test-build:
	$(eval BRANCH = test)
	docker build -t $(IMAGE_NAME) .

test: test-build run-test
single-test: test-build run-test
e2e-test: e2e-network-check e2e-run-chrome test-build
	-docker rm ella-e2e
	docker run -v errorShots:/ella/errorShots/ --name ella-e2e --network=local_only --link chromebox:cb $(IMAGE_NAME) make e2e-run-ci
e2e-test-local: test-build
	-docker rm ella-e2e-local
	docker run --name ella-e2e-local -it -v $(shell pwd):/ella -p 5000:5000 -p 5859:5859 $(IMAGE_NAME) /bin/bash -c "make e2e-ella; echo \"Run 'make wdio' to run e2e tests\"; /bin/bash"

run-test:
	docker run $(IMAGE_NAME) make test-$(TEST_NAME) TEST_COMMAND=$(TEST_COMMAND)

e2e-ella:
	supervisord -c /ella/ops/test/supervisor-e2e.cfg
	make dbsleep

e2e-run-ci: e2e-ella wdio-chromebox

wdio-chromebox:
	/dist/node_modules/webdriverio/bin/wdio --baseUrl "ella-e2e:5000" --host "cb" --port 4444 --path "/" /ella/src/webui/tests/e2e/wdio.conf.js

wdio:
	DEBUG=true /dist/node_modules/webdriverio/bin/wdio $(WDIO_OPTIONS) --baseUrl $(APP_BASE_URL) --host $(CHROME_HOST) --port 4444 --path "/" /ella/src/webui/tests/e2e/wdio.conf.js

e2e-run-chrome:
	-docker kill chromebox
	-docker rm chromebox
	docker run -d --name chromebox --network=local_only ousamg/chromebox

e2e-network-check:
	docker network ls | grep -q local_only || docker network create --subnet 172.25.0.0/16 local_only

#---------------------------------------------
# TESTING - INSIDE CONTAINER ONLY
#---------------------------------------------
.PHONY: test-all test-api test-api-migration test-common test-js test-e2e

test-all: test-js test-common test-api

test-api: export PGDATABASE=vardb-test
test-api: export DB_URL=postgres:///vardb-test
test-api: export PYTHONPATH=/ella/src
test-api:
	supervisord -c /ella/ops/test/supervisor.cfg
	make dbsleep
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
test-api-migration:
	supervisord -c /ella/ops/test/supervisor.cfg
	make dbsleep
	createdb vardb-test
ifeq ($(TEST_COMMAND),) # empty?
	# Run migration scripts test
	/ella/ella-cli database ci-migration

	# Run API test on migrated database
	/ella/ella-cli database ci-migration-head
	py.test --color=yes "/ella/src/api/" -s
else
	$(TEST_COMMAND)
endif

test-common: export PGDATABASE=vardb-test
test-common: export DB_URL=postgres:///vardb-test
test-common: export PYTHONPATH=/ella/src
test-common:
	supervisord -c /ella/ops/test/supervisor.cfg
	make dbsleep
	createdb vardb-test
	/ella/ella-cli database drop -f
	/ella/ella-cli database make -f
ifeq ($(TEST_COMMAND),) # empty?
	py.test src -k 'not test_ui' --color=yes --cov src --cov-report xml --ignore src/api
else
	$(TEST_COMMAND)
endif

test-js:
	rm -f /ella/node_modules
	ln -s /dist/node_modules/ /ella/node_modules
	gulp unit

