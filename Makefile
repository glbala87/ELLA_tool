# This file should be in charge of any short-lived processes
# Anything long-running should be controlled by supervisord
.PHONY: build test-api test-common test-js cleanup-ownership test dev

BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)
API_PORT ?= 8000-9999

docker-build:
	docker build -t local/gin-$(BRANCH) .

docker-run-dev:
	docker run -d \
	--name gin-$(BRANCH)-$(USER) \
	-p $(API_PORT):5000 \
	$(GIN_OPTS) \
	-v $(shell pwd):/genap \
	local/gin-$(BRANCH) \
	supervisord -c /genap/ops/dev/supervisor.cfg

docker-run-tests:
	docker run -v `pwd`:/genap local/gin-test make all-tests

test: build docker-run-tests

build: docker-build

dev: docker-run-dev

all-tests: test-js test-common test-api cleanup-ownership

test-api: export DB_URL=postgres:///postgres
test-api: export PYTHONPATH=/genap/src
test-api:
	supervisord -c /genap/ops/test/supervisor.cfg
	py.test "/genap/src/api" -s

test-common: export PYTHONPATH=/genap/src
test-common:
	py.test src -k 'not test_ui' --cov src --cov-report xml --ignore src/api

test-js:
	rm -f /genap/node_modules
	ln -s /dist/node_modules/ /genap/node_modules
	gulp unit

cleanup-ownership:
	chown -R $(USER) .

