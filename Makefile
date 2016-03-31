.PHONY: any help build dev kill shell logs restart test-build test single-test run-test e2e-test run-e2e-test run-e2e-selenium run-e2e-app cleanup-e2e test-all test-api test-common test-js test-e2e set-release-var release dev-release create-release get-ansible run-ansible commit-provision stop-provision clean-ansible

BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)
ANY = $(shell docker ps | awk '/ella-.*-$(USER)/ {print $$NF}')
API_PORT ?= 8000-9999
INTERNAL_API_PORT = 5000 # e2e testing uses linked containers, so use container internal port
INTERNAL_SELENIUM_PORT = 4444 # e2e testing uses linked containers, so use container internal port
API_HOST ?= 'localhost'
TEST_NAME ?= all
CONTAINER_NAME = ella-$(BRANCH)-$(USER)
IMAGE_NAME = local/ella-$(BRANCH)
E2E_CONTAINER_NAME = ella-e2e-$(BRANCH)-$(USER)
SELENIUM_CONTAINER_NAME = selenium
SELENIUM_ADDRESS ?= 'http://localhost:4444/wd/hub'
BUILD_TYPE ?= core
BUILD_VERSION ?= 0.9.1

help :
	@echo ""
	@echo "-- DEV COMMANDS --"
	@echo "make build		- build image $(IMAGE_NAME)"
	@echo "make dev		- run image $(IMAGE_NAME), with container name $(CONTAINER_NAME) :: API_PORT and ELLA_OPTS available as variables"
	@echo "make kill		- stop and remove $(CONTAINER_NAME)"
	@echo "make shell		- get a bash shell into $(CONTAINER_NAME)"
	@echo "make logs		- tail logs from $(CONTAINER_NAME)"
	@echo "make restart		- restart container $(CONTAINER_NAME)"
	@echo "make any		- can be prepended to target the first container with pattern ella-.*-$(USER), e.g. make any kill"
	@echo ""
	@echo "-- TEST COMMANDS --"
	@echo "make test		- build image local/ella-test, then run all tests"
	@echo "make single-test	- build image local/ella-test :: TEST_NAME={api | common | js } required as variable or will default to 'all'"
	@echo "make e2e-test		- build image local/ella-test, then run e2e tests"
	@echo ""
	@echo "-- RELEASE COMMANDS --"
	@echo "make dev-release	- builds a development image named ousamg/ella-$(BUILD_TYPE):$(BUILD_VERSION)"
	@echo "make release		- builds a production image named ousamg/ella-release:$(BUILD_VERSION)"

#---------------------------------------------
# DEVELOPMENT
#---------------------------------------------

any:
	$(eval CONTAINER_NAME = $(ANY))
	@true

build:
	docker build -t $(IMAGE_NAME) .

dev:
	docker run -d \
	--name $(CONTAINER_NAME) \
	-p $(API_PORT):5000 \
	$(ELLA_OPTS) \
	-v $(shell pwd):/ella \
	$(IMAGE_NAME) \
	supervisord -c /ella/ops/dev/supervisor.cfg

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

test-build:
	$(eval BRANCH = test)
	sed 's/# ADD/ADD/' Dockerfile > Dockerfile.test
	docker build -t $(IMAGE_NAME) -f Dockerfile.test .
	rm Dockerfile.test

test: test-build run-test
single-test: test-build run-test
e2e-test: test-build run-e2e-app run-e2e-selenium run-e2e-test cleanup-e2e

run-test:
	docker run $(IMAGE_NAME) make test-$(TEST_NAME)

# test runner (protractor) for e2e tests
run-e2e-test:
	docker run --link $(SELENIUM_CONTAINER_NAME):selenium --rm --name e2e $(IMAGE_NAME) make test-e2e API_PORT=$(INTERNAL_API_PORT) API_HOST=genapp SELENIUM_ADDRESS=http://selenium:$(strip $(INTERNAL_SELENIUM_PORT))/wd/hub

run-e2e-selenium:
	docker run --name $(SELENIUM_CONTAINER_NAME) --link $(E2E_CONTAINER_NAME):genapp -d -p 4444:$(INTERNAL_SELENIUM_PORT) -p 5900:5900 -v /dev/shm:/dev/shm selenium/standalone-chrome-debug:2.48.2
	sleep 5

# not re-using dev runner here because we don't want image mounting
run-e2e-app:
	docker run -d \
	--name $(E2E_CONTAINER_NAME) \
	-p $(API_PORT):$(INTERNAL_API_PORT) \
	$(ELLA_OPTS) \
	$(IMAGE_NAME) \
	supervisord -c /ella/ops/dev/supervisor.cfg
	sleep 10

cleanup-e2e:
	-docker stop $(SELENIUM_CONTAINER_NAME)
	-docker rm $(SELENIUM_CONTAINER_NAME)
	-docker stop $(E2E_CONTAINER_NAME)
	-docker rm $(E2E_CONTAINER_NAME)

#---------------------------------------------
# TESTING - INSIDE CONTAINER ONLY
#---------------------------------------------

test-all: test-js test-common test-api

test-api: export PGDATABASE=vardb-test
test-api: export DB_URL=postgres:///vardb-test
test-api: export PYTHONPATH=/ella/src
test-api:
	supervisord -c /ella/ops/test/supervisor.cfg
	sleep 5
	py.test "/ella/src/api" -s

test-common: export PYTHONPATH=/ella/src
test-common:
	py.test src -k 'not test_ui' --cov src --cov-report xml --ignore src/api

test-js:
	rm -f /ella/node_modules
	ln -s /dist/node_modules/ /ella/node_modules
	gulp unit

# preq: app and selenium are already started
test-e2e:
	@echo "Running e2e tests against $(API_HOST):$(API_PORT) using selenium server $(SELENIUM_ADDRESS)"
	rm -f /ella/node_modules
	ln -s /dist/node_modules/ /ella/node_modules
	gulp --e2e_ip=$(API_HOST) --e2e_port=$(API_PORT) --selenium_address=$(SELENIUM_ADDRESS) e2e


#---------------------------------------------
# RELEASES
#---------------------------------------------

set-release-var:
	$(eval BUILD_TYPE = release)

ensure-clean: clean-ansible
	rm -rf node_modules

define DOCKERFILE
FROM ousamg/ella-release:$(BUILD_VERSION)
RUN ln -sf /dev/stdout /var/log/nginx.access
EXPOSE 80
WORKDIR /ella
ENTRYPOINT ["supervisord", "-c", "/ella/ops/prod/supervisor.cfg"]
endef
export DOCKERFILE
create-dockerfile-runnable:
	echo "$$DOCKERFILE" > ops/builder/Dockerfile.runnable
build-dockerfile-runnable:
	docker build -t ousamg/ella:$(BUILD_VERSION) -f ops/builder/Dockerfile.runnable .
remove-dockerfile-runnable:
	rm -rf ops/builder/Dockerfile.runnable

release: set-release-var ensure-clean create-prod-file start-provision remove-prod-file create-release create-dockerfile-runnable build-dockerfile-runnable remove-dockerfile-runnable
dev-release: start-provision create-release
create-release: get-ansible run-ansible commit-provision stop-provision clean-ansible

create-prod-file:
	sed -i 's/# ADD/ADD/' ops/builder/Dockerfile

remove-prod-file:
	git checkout ops/builder/Dockerfile

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
	docker commit provision ousamg/ella-$(BUILD_TYPE):$(BUILD_VERSION)

stop-provision:
	docker ps | grep -q provision && docker stop -t 0 provision && docker rm provision
	docker rmi -f init

#---------------------------------------------
# DEPLOY
#---------------------------------------------

deploy-release: release deploy-reboot

deploy-reboot:
	-docker stop ella
	-docker rm ella
	docker run -d --name ella -p 80:80 ousamg/ella:$(BUILD_VERSION)
