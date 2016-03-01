# This file should be in charge of any short-lived processes
# Anything long-running should be controlled by supervisord
.PHONY: docker-build docker-run-dev docker-run-tests restart logs test build dev all-tests test-api test-common test-js

BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)
API_PORT ?= 8000-9999
CONTAINER_NAME = gin-$(BRANCH)-$(USER)
IMAGE_NAME = local/gin-$(BRANCH)
BUILD_TYPE ?= core
BUILD_VERSION ?= 0.9.1

help :
	@echo ""
	@echo "-- GENERAL COMMANDS --"
	@echo "make build		- build image $(IMAGE_NAME)"
	@echo "make kill		- stop and remove $(CONTAINER_NAME)"
	@echo ""
	@echo "-- DEV COMMANDS --"
	@echo "make dev		- run image $(IMAGE_NAME), with container name $(CONTAINER_NAME) :: API_PORT and GIN_OPTS available as variables"
	@echo "make shell		- get a bash shell into $(CONTAINER_NAME)"
	@echo "make logs		- tail logs from $(CONTAINER_NAME)"
	@echo "make restart		- restart container $(CONTAINER_NAME)"
	@echo ""
	@echo "-- TEST COMMANDS --"
	@echo "make test		- build image $(IMAGE_NAME), then run all tests in a new container"
	@echo "make single-test	- run image $(IMAGE_NAME) :: TEST_NAME={api | common | js} available as variable"

docker-build:
	docker build -t $(IMAGE_NAME) .

# NOTE: you should not run this directly!
#       see instead: ci-build
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
	docker run $(IMAGE_NAME) make all-tests

docker-run-single-test:
	docker run -v `pwd`:/genap $(IMAGE_NAME) make test-$(TEST_NAME)

restart:
	docker restart $(CONTAINER_NAME)

logs:
	docker logs -f $(CONTAINER_NAME)

shell:
	docker exec -it $(CONTAINER_NAME) bash

kill:
	docker stop $(CONTAINER_NAME)
	docker rm $(CONTAINER_NAME)

test: ci-build docker-run-tests

build: docker-build
ci-build: create-ci-file docker-build-self-contained kill-ci-file
create-ci-file:
	sed 's/# ADD/ADD/' Dockerfile > Dockerfile.ci
kill-ci-file:
	rm Dockerfile.ci

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

image: start-provision get-ansible run-ansible commit-provision stop-provision clean-ansible
get-ansible:
	virtualenv ops/builder/venv
	ops/builder/venv/bin/pip install --upgrade ansible
run-ansible:
	ops/builder/venv/bin/ansible-playbook -i provision, -c docker ops/builder/builder.yml --tags=$(BUILD_TYPE)
clean-ansible:
	rm -rf ops/builder/venv
start-provision:
	docker ps | grep -q provision && docker stop -t 0 provision && docker rm provision || exit 0
	docker build -t init -f ops/builder/Dockerfile .
	docker run -d --name provision init sleep infinity
commit-provision:
	docker commit provision ousamg/gin-$(BUILD_TYPE):$(BUILD_VERSION)
stop-provision:
	docker ps | grep -q provision && docker stop -t 0 provision && docker rm provision
	docker rmi -f init
