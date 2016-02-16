# This file should be in charge of any short-lived processes
# Anything long-running should be controlled by supervisord
.PHONY: docker-build docker-run-dev docker-run-tests restart logs test build dev all-tests test-api test-common test-js

BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)
API_PORT ?= 8000-9999
CONTAINER_NAME = gin-$(BRANCH)-$(USER)
IMAGE_NAME = local/gin-$(BRANCH)

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
	@echo "make single-test	- run image $(IMAGE_NAME) :: TEST_NAME={api | common | js} available as variable"

docker-build:
	docker build -t $(IMAGE_NAME) .

docker-build-self-contained:
	docker build -t $(IMAGE_NAME) -f Dockerfile.ci .

docker-run-dev:
	docker run -d \
	--name $(CONTAINER_NAME) \
	-p $(API_PORT):5000 \
	$(GIN_OPTS) \
	-v $(shell pwd):/genap \
	$(IMAGE_NAME) \
	supervisord -c /genap/ops/dev/supervisor.cfg

docker-run-tests:
	docker run -v `pwd`:/genap $(IMAGE_NAME) make all-tests

docker-run-single-test:
	docker run -v `pwd`:/genap $(IMAGE_NAME) make test-$(TEST_NAME)

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

test-api: export DB_URL=postgres:///postgres
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
