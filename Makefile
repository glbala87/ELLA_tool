# This file should be in charge of any short-lived processes
# Anything long-running should be controlled by supervisord
.PHONY: docker-build docker-run-dev docker-run-tests restart logs test build dev all-tests test-api test-common test-js

BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)
API_PORT ?= 8000-9999
API_HOST ?= 'http://localhost'
SELENIUM_ADDRESS ?= 'http://172.16.250.128:4444/wd/hub'

CONTAINER_NAME = gin-$(BRANCH)-$(USER)
E2E_CONTAINER_NAME = gin-e2e-$(BRANCH)-$(USER)
SELENIUM_CONTAINER_NAME = selenium
IMAGE_NAME = local/gin-$(BRANCH)
SELENIUM_ADDRESS ?= 'http://localhost:4444/wd/hub'

help :
	@echo ""
	@echo "-- GENERAL COMMANDS --"
	@echo "make build		- build image $(IMAGE_NAME)"
	@echo ""
	@echo "-- DEV COMMANDS --"
	@echo "make dev		- run image $(IMAGE_NAME), with container name $(CONTAINER_NAME) :: API_PORT and GIN_OPTS available as variables"
	@echo "make logs		- tail logs from $(CONTAINER_NAME)"
	@echo "make restart		- restart container $(CONTAINER_NAME)"
	@echo ""
	@echo "-- TEST COMMANDS --"
	@echo "make test		- build image $(IMAGE_NAME), then run all tests in a new container"
	@echo "make single-test	- run image $(IMAGE_NAME) :: TEST_NAME={api | common | js } available as variable"
	@echo "make test-e2e-main - starts/stops selenium container, run test against a running app"

docker-build:
	docker build -t $(IMAGE_NAME) .

docker-build-self-contained:
	docker build -t $(IMAGE_NAME) -f Dockerfile.ci .

docker-run-e2e-app: e2e-config docker-run-dev

e2e-config:
	$(eval CONTAINER_NAME :=$(E2E_CONTAINER_NAME))


docker-run-dev:
	docker run -d \
	--name $(CONTAINER_NAME) \
	-p $(API_PORT):5000 \
	$(GIN_OPTS) \
	-v $(shell pwd):/genap \
	$(IMAGE_NAME) \
	supervisord -c /genap/ops/dev/supervisor.cfg

docker-run-tests:
	docker run $(IMAGE_NAME) make all-tests

docker-run-single-test:
	docker run -v `pwd`:/genap $(IMAGE_NAME) make test-$(TEST_NAME)

docker-run-e2e-test:
	docker run --rm -v `pwd`:/genap $(IMAGE_NAME) make test-e2e API_PORT=$(API_PORT) API_HOST=$(API_HOST) SELENIUM_ADDRESS=$(SELENIUM_ADDRESS)

restart:
	docker restart $(CONTAINER_NAME)

logs:
	docker logs -f $(CONTAINER_NAME)

test: ci-build docker-run-tests

build: docker-build
ci-build: docker-build-self-contained

dev: docker-run-dev

all-tests: test-js test-common test-api
single-test: docker-run-single-test

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

test-e2e:
	@echo $(API_HOST) $(API_PORT)
	rm -f /genap/node_modules
	ln -s /dist/node_modules/ /genap/node_modules
	gulp --e2e_ip=$(API_HOST) --e2e_port=$(API_PORT) e2e
#	gulp --e2e_ip=localhost --e2e_port=$(API_PORT) --selenium_address=$(SELENIUM_ADDRESS) e2e
#	gulp e2e

docker-selenium-start:
	docker run --name $(SELENIUM_CONTAINER_NAME) -d -p 4444:4444 -p 5900:5900 -v /dev/shm:/dev/shm selenium/standalone-chrome-debug:2.48.2

test-e2e-main: docker-run-e2e-app docker-selenium-start docker-run-e2e-test
	docker stop $(SELENIUM_CONTAINER_NAME)
	docker rm $(SELENIUM_CONTAINER_NAME)
	docker stop $(E2E_CONTAINER_NAME)
	docker rm $(E2E_CONTAINER_NAME)
