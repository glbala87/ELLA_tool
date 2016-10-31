BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)
API_PORT ?= 8000-9999
INTERNAL_API_PORT = 5000 # e2e testing uses linked containers, so use container internal port
INTERNAL_SELENIUM_PORT = 4444 # e2e testing uses linked containers, so use container internal port
API_HOST ?= 'localhost'
TEST_NAME ?= all
TEST_COMMAND ?=''
CONTAINER_NAME ?= ella-$(BRANCH)-$(USER)
IMAGE_NAME = local/ella-$(BRANCH)
E2E_CONTAINER_NAME = ella-e2e-$(BRANCH)-$(USER)
SELENIUM_CONTAINER_NAME = selenium
SELENIUM_ADDRESS ?= 'http://localhost:4444/wd/hub'

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
	@echo "make single-test	- build image local/ella-test :: TEST_NAME={api | common | js } required as variable or will default to 'all'"
	@echo "                          optional variable TEST_COMMAND=... will override the py.test command"
	@echo " 			  Example: TEST_COMMAND=\"'py.test --exitfirst \"/ella/src/api/util/tests/test_sanger*\" -s'\""
	@echo "make e2e-test		- build image local/ella-test, then run e2e tests"
	@echo ""
	@echo "-- RELEASE COMMANDS --"
	@echo "make core		- builds a core (development) image named ousamg/ella-core"
	@echo "make release		- builds a production image named ousamg/ella-release"

#---------------------------------------------
# DEVELOPMENT
#---------------------------------------------
.PHONY: any build dev fancy-dev url kill shell logs restart db

any:
	$(eval CONTAINER_NAME = $(shell docker ps | awk '/ella-.*-$(USER)/ {print $$NF}'))
	@true

build:
	docker build --pull -t $(IMAGE_NAME) .

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
	docker exec $(CONTAINER_NAME) make dbreset

url:
	@./ops/dev/show-url.sh

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
.PHONY: test-build test single-test e2e-test run-test run-e2e-test run-e2e-selenium run-e2e-app cleanup-e2e

test-build:
	$(eval BRANCH = test)
	sed 's/# COPY/COPY/' Dockerfile > Dockerfile.test
	docker build -t $(IMAGE_NAME) -f Dockerfile.test .
	rm Dockerfile.test

test: test-build run-test
single-test: test-build run-test
e2e-test: e2e-network-check e2e-run-chrome test-build
	-docker rm ella-e2e
	docker run -v errorShots:/ella/errorShots/ --name ella-e2e --network=local_only --link chromebox:cb $(IMAGE_NAME) make e2e-run-ci
e2e-test-local: test-build
	docker run --name ella-e2e-local -it -v $(shell pwd):/ella -p 5000:5000 -p 5859:5859 $(IMAGE_NAME) /bin/bash -c "make e2e-ella; echo \"Run 'make wdio' to run e2e tests\"; /bin/bash"

run-test:
	docker run $(IMAGE_NAME) make test-$(TEST_NAME) TEST_COMMAND=$(TEST_COMMAND)

e2e-ella:
	supervisord -c /ella/ops/test/supervisor-e2e.cfg
	make dbsleep

e2e-run-ci: e2e-ella wdio-chromebox

wdio-chromebox:
	/dist/node_modules/webdriverio/bin/wdio --baseUrl "http://ella-e2e:5000" --host "cb" --port 4444 --path "/" /ella/src/webui/tests/e2e/wdio.conf.js

wdio:
	DEBUG=true /dist/node_modules/webdriverio/bin/wdio --baseUrl "http://localhost:5000" --host "172.17.0.1" --port 4444 --path "/" /ella/src/webui/tests/e2e/wdio.conf.js

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
ifeq ($(TEST_COMMAND),) # empty?

	/ella/ella-cli database drop -f
	/ella/ella-cli database make -f
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

test-common: export PYTHONPATH=/ella/src
test-common:
ifeq ($(TEST_COMMAND),) # empty?
	py.test src -k 'not test_ui' --color=yes --cov src --cov-report xml --ignore src/api
else
	$(TEST_COMMAND)
endif

test-js:
	rm -f /ella/node_modules
	ln -s /dist/node_modules/ /ella/node_modules
	gulp unit

#---------------------------------------------
# BUILD / RELEASE
#---------------------------------------------
BUILD_VERSION ?= should_not_happen
ANSIBLE_TAGS ?= core
BUILD_TYPE ?= core
BUILD_NAME ?= ousamg/ella.$(BUILD_TYPE):$(BUILD_VERSION)
.PHONY: setup-release setup-core ensure-clean add-production-elements release build-image core push squash copy run-ansible clean-provision stop-provision start-provision commit-provision

setup-core:
	$(eval BUILD_VERSION = $(shell awk -F':' '/ella.core/ { print $$2 }' Dockerfile))
	$(eval CORE_NAME := ousamg/baseimage:latest)

setup-release: ensure-clean
	$(eval ANSIBLE_TAGS = release)
	$(eval BUILD_TYPE = release)
	$(eval BUILD_VERSION =latest)
	$(eval CORE_NAME = $(shell awk '/ella.core/ { print $$2 }' Dockerfile))

ensure-clean:
	rm -rf node_modules
	git checkout ops/builder/Dockerfile.runnable

add-production-elements:
	sed -i 's substitution $(BUILD_NAME) ' ops/builder/Dockerfile.runnable
	docker build -t $(BUILD_NAME) -f ops/builder/Dockerfile.runnable .
	git checkout ops/builder/Dockerfile.runnable

release: setup-release build-image squash stop-provision add-production-elements
build-image: start-provision copy run-ansible
core: setup-core build-image commit-provision stop-provision

push:
	docker push $(BUILD_NAME)

squash:
	docker export provision | docker import - $(BUILD_NAME)

copy:
	docker cp . provision:/ella

run-ansible:
	docker exec -i provision ansible-playbook -i localhost, -c local /ella/ops/builder/builder.yml --tags=$(ANSIBLE_TAGS)

clean-provision stop-provision:
	-docker stop -t 0 provision && docker rm provision

start-provision: clean-provision
	docker pull $(CORE_NAME)
	docker run -d --name provision $(CORE_NAME) sleep infinity

commit-provision:
	docker commit provision $(BUILD_NAME)

#---------------------------------------------
# DEPLOY
#---------------------------------------------
comma := ,
DEPLOY_NAME ?= test.allel.es
.PHONY: tsd-assets dbreset dbreset-inner dbsleep deploy

tsd-assets:
	docker run -d --name ella-assets ousamg/ella.release
	docker cp ella-assets:/static .
	docker stop ella-assets
	docker rm ella-assets

dbreset: dbsleep dbreset-inner

dbreset-inner:
	bash -c "DB_URL='postgresql:///postgres' PYTHONIOENCODING='utf-8' RESET_DB='small' python src/api/main.py"

dbsleep:
	while ! pg_isready; do sleep 5; done

deploy:
	-docker stop $(subst $(comma),-,$(DEPLOY_NAME))
	-docker rm $(subst $(comma),-,$(DEPLOY_NAME))
	docker run -d --name $(subst $(comma),-,$(DEPLOY_NAME)) -e VIRTUAL_HOST=$(DEPLOY_NAME) --expose 80 ousamg/ella.$(BUILD_TYPE)
	docker exec $(subst $(comma),-,$(DEPLOY_NAME)) make dbreset
