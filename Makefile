# This file should be in charge of any short-lived, inter-container processes
	# Anything meant to be run outside of Docker should be in an executable
	# Anything long-running should be controlled by supervisord

test-api: export DB_URL=postgres:///postgres
test-api: export PYTHONPATH=/genap/src
test-api:
	supervisord -c /genap/ops/test/supervisor.cfg
	py.test "/genap/src/api" -s

test-common: export PYTHONPATH=/genap/src
test-common:
	py.test src -k 'not test_ui' --cov src --cov-report xml --ignore src/api

test-js:
	gulp unit

cleanup-ownership:
	chown -R $(USER) .

test: test-js test-common test-api cleanup-ownership
