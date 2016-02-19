# This file should be in charge of any short-lived processes
# Anything long-running should be controlled by supervisord
.PHONY: build ci-build docker-build docker-build-self-contained \
dev docker-run-dev restart logs \
ci-single-test ci-e2e-test single-test \
docker-run-all-tests docker-run-single-test ci-docker-run-single-test ci-docker-run-e2e-test  \
ci-docker-selenium docker-run-e2e-app  docker-cleanup-e2e \
check_test_name all-tests test-api test-common test-js test-e2e \
 

BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)
API_PORT ?= 8000-9999
INTERNAL_API_PORT = 5000# e2e testing uses linked containers, so use container internal port
INTERNAL_SELENIUM_PORT = 4444# e2e testing uses linked containers, so use container internal port
API_HOST ?= 'localhost'

CONTAINER_NAME = gin-$(BRANCH)-$(USER)
E2E_CONTAINER_NAME = gin-e2e-$(BRANCH)-$(USER)
SELENIUM_CONTAINER_NAME = selenium
IMAGE_NAME = local/gin-$(BRANCH)
SELENIUM_ADDRESS ?= 'http://localhost:4444/wd/hub'

help :
	@echo ""
	@echo "-- GENERAL COMMANDS --"
	@echo "make build		     - build image $(IMAGE_NAME)"
	@echo ""
	@echo "-- DEV COMMANDS --"
	@echo "make dev		         - run image $(IMAGE_NAME), with container name $(CONTAINER_NAME) :: API_PORT and GIN_OPTS available as variables"
	@echo "make peek		     - exec into the container $(CONTAINER_NAME)"
	@echo "make logs		     - tail logs from $(CONTAINER_NAME)"
	@echo "make restart		     - restart container $(CONTAINER_NAME)"
	@echo ""
	@echo "-- TEST COMMANDS --"
	@echo "make test		     - build image $(IMAGE_NAME), then run all tests in a new container"
	@echo "make single-test	     - run image $(IMAGE_NAME) :: TEST_NAME={api | common | js } available as variable"
	@echo ""
	@echo "-- CI TEST COMMANDS --"
	@echo "make ci-single-test          - runs a single type of test :: TEST_NAME={ api | common | js } available as variable"
	@echo "make ci-e2e-test             - runs e2e tests using a running g:n app. Starts/stops containers for app, selenium and protractor (test runner)"
	

#---------------------------------------------
# Container building
#---------------------------------------------

build: docker-build

ci-build: docker-build-self-contained

docker-build:
	docker build -t $(IMAGE_NAME) .

docker-build-self-contained:
	docker build -t $(IMAGE_NAME) -f Dockerfile.ci .

#---------------------------------------------
# Local development
#---------------------------------------------

dev: docker-run-dev

restart:
	docker restart $(CONTAINER_NAME)

logs:
	docker logs -f $(CONTAINER_NAME)

peek:
	docker exec -it $(CONTAINER_NAME) bash
# the following targets are to be called by other targets only:

docker-run-dev:
	docker run -d \
	--name $(CONTAINER_NAME) \
	-p $(API_PORT):5000 \
	$(GIN_OPTS) \
	-v $(shell pwd):/genap \
	$(IMAGE_NAME) \
	supervisord -c /genap/ops/dev/supervisor.cfg


#---------------------------------------------
# Start containers to run tests
#---------------------------------------------

ci-single-test: check_test_name ci-build ci-docker-run-single-test # run a specific test type in ci (common, js, api): make test-$(TEST_NAME)

ci-e2e-test: ci-build docker-run-e2e-app ci-docker-run-e2e-test # starts containers and cleans up
	make docker-cleanup-e2e

single-test: docker-run-single-test

test: docker-run-all-tests


# the following targets are to be called by other targets only:
 
docker-run-all-tests:
	docker run $(IMAGE_NAME) make all-tests

ci-docker-run-single-test: check_test_name
	docker run $(IMAGE_NAME) make test-$(TEST_NAME)

docker-run-single-test: check_test_name
	docker run -v `pwd`:/genap $(IMAGE_NAME) make test-$(TEST_NAME)

ci-docker-run-e2e-test: ci-docker-selenium # test runner (protractor) for e2e tests
	docker run --link $(SELENIUM_CONTAINER_NAME):selenium --rm --name e2e $(IMAGE_NAME) make test-e2e API_PORT=$(INTERNAL_API_PORT) API_HOST=genapp SELENIUM_ADDRESS=http://selenium:$(INTERNAL_SELENIUM_PORT)/wd/hub \
	|| (ret=$$?; echo "Failure. Will remove containers" && make docker-cleanup-e2e && exit $$ret)

ci-docker-selenium:
	docker run --name $(SELENIUM_CONTAINER_NAME) --link $(E2E_CONTAINER_NAME):genapp -d -p 4444:$(INTERNAL_SELENIUM_PORT) -p 5900:5900 -v /dev/shm:/dev/shm selenium/standalone-chrome-debug:2.48.2
	sleep 5

docker-run-e2e-app: # container used when doing e2e tests. No volume mounting, so file changes when developing won't be picked up!
	docker run -d \
	--name $(E2E_CONTAINER_NAME) \
	-p $(API_PORT):$(INTERNAL_API_PORT) \
	$(GIN_OPTS) \
	$(IMAGE_NAME) \
	supervisord -c /genap/ops/dev/supervisor.cfg
	sleep 10

check_test_name:
		@if [ "$(TEST_NAME)" == "" ] ; then echo "Please specify TEST_NAME"; exit 1 ; fi

docker-cleanup-e2e:
	docker stop $(SELENIUM_CONTAINER_NAME)
	docker rm $(SELENIUM_CONTAINER_NAME)
	docker stop $(E2E_CONTAINER_NAME)
	docker rm $(E2E_CONTAINER_NAME)

#---------------------------------------------
# Test targets inside containers:
#---------------------------------------------

# the following targets are to be called by other targets only:
 
all-tests: test-js test-common test-api

test-api: export PGDATABASE=vardb-test
test-api: export DB_URL=postgres:///vardb-test
test-api: export PYTHONPATH=/genap/src
test-api:
	supervisord -c /genap/ops/test/supervisor.cfg
	sleep 5
	py.test "/genap/src/api" -s


test-common: export PYTHONPATH=/genap/src
test-common:
	py.test src -k 'not test_ui' --cov src --cov-report xml --ignore src/api


test-js:
	rm -f /genap/node_modules
	ln -s /dist/node_modules/ /genap/node_modules
	gulp unit


test-e2e: # preq: app and selenium are already started
	@echo "Running e2e tests against $(API_HOST):$(API_PORT) using selenium server $(SELENIUM_ADDRESS)"
	rm -f /genap/node_modules
	ln -s /dist/node_modules/ /genap/node_modules
	gulp --e2e_ip=$(API_HOST) --e2e_port=$(API_PORT) --selenium_address=$(SELENIUM_ADDRESS) e2e

