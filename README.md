ella is a web app based on AngularJS with a Flask REST backend.

Most functionality is now baked into a Makefile, run `make help` to see a quick overview of available commands.

# Development

### Getting started:
- Start a development environment in Docker, run **`make dev`** - you may need to do `make build` first
- Populate the database by visiting the `/reset` route _or do `/reset?testset=all` to get an expanded data set_.

### More info:
- All *system* dependencies - as in apt-packages
  - are kept in core images (e.g. `ousamg/ella-core:0.9.1`)
  - are managed via the build system `ops/builder/builder.yml`
- All *application* dependencies - nodejs, python, etc.
  - are kept in local images (e.g. `local/ella-dev`)
  - are managed via their respective dependency files
  - are baked in when you do `make build`, so if you change a dependency file you need to do `make build` again!

### Migration:
Whenever you make changes to the database model, you need to create migration scripts, so that the production database can be upgraded to the new version. We use Alembic to assist creating those scripts. Migration scripts are stored in `src/vardb/datamodel/migration/alembic/`. The current migration base is stored in `src/vardb/datamodel/migration/ci_migration_base`. This base serves as the base for which the migration scripts will be built against, and should represent the oldest database in production.

To create a new migration:

1. Make all your changes to the normal datamodel in `src/vardb/datamodel/` and test them until you're satisfied. In general we don't want to make more migration scripts than necessary, so make sure things are proper.
1. On your dev instance, run `./ella-cli database ci-migration-head` to reset the database to the migration base, then run all the upgrades to make
1. `cd src/vardb/datamodel/migration/` and run something like this `PYTHONPATH=../../.. DB_URL=postgresql://postgres@/postgres alembic revision --autogenerate -m "Name of migration"`. This will look at the current datamodel and compare it against the database state, generating a migration script from the differences.
1. Go over the created script, clean it up and test it. The migration scripts are far from perfect, so you need some knowledge of SQLAlchemy and Postgres to get it right. Known issues are `Sequences` and `ENUM`s, which have to be taken care of manually. Also remember to convert any data present in the database if necessary. The `test-api-migration` part of the test suite will test also test database migrations, by running the api tests on a migrated database.


### API documentation

The API is documented using [apidocs](https://apispec.readthedocs.io/en/latest/) supporting the OpenAPI specification (f.k.a. Swagger 2.0).
You can see the specification [here](http://swagger.io/specification/).

You can explore the ella's API at `/api/v1/docs/` in you browser.

To document your resource, have a look at the current resources to see usage examples.

Under the hood, the resources and definitions (models) are loaded into `apispec` in `api/v1/docs.py`. The spec is made available at `/api/v1/specs/`.
The definitions are generated automatically by `apispec` using it's Marshmallow plugin.

# Testing

Our test suites are intended to be run inside Docker. The Makefile has commands to do run setup and the tests themselves.

## Getting started
- `make test` will run all (js, api, and common) tests _excluding e2e tests_
- `make e2e-test` will run e2e tests
- `make single-test` will run a single _non-e2e_ test

To clean up docker containers when e2e tests fail: `make cleanup-e2e BRANCH=test`

## More info
- For more information please see [the wiki](https://git.ousamg.io/docs/wiki/wikis/ella/testing)

# Production

### Getting started:
- Start the app using `docker run -p 80:80 -d ousamg/ella`
- You may also want to mount the following folders:
  - `/logs` - application logs
  - `/data` - database storage

### More info:
- nginx is used to serve both the API and static assets
  - Static assets are pre-built and stored at `/static`
  - Gunicorn runs the API, it stores its socket at `/socket`
- All relevant configuration files are in `ops/prod`

# Protractor - e2e testing tool
Protractor is an Angular friendly wrapper around WebDriver. 
See http://www.protractortest.org

The e2e tests usually run in Docker (see the Makefile) and modules are found in the node_modules folder inside Docker.
If you want to run it outside Docker, we'll create a node_modules folder inside our src/webui/tests folder.
This allows node to find the required modules/classes in 'node_modules' and our src/webui/tests folder.

## Setup
In src/webui/tests:
- Run `npm install` to install modules
- Then `npm run-script init` to install selenium/webdriver

Several scripts are defined in package.json. Having this indirection ensures that the locally installed binaries in node_modules are used.
Running bare `protractor` (as opposed to `npm run-script protractor`) will use your globally installed protractor (if you have one) and could cause 'library not found'-errors.
There are several scripts in package.json that calls protractor with a few hardcoded arguments. Use the script `protractor` if you want to call protractor with your arguments of choice.
All arguments after '--' are passed to the script. So `npm run-script myScript -- --myOption cool` will run 'myScript' passing it '--myOption cool'.


## Interact with webpage:
Start a Repl:	
`npm run-script repl --  --baseUrl <url to your running app>`

This opens a new Chrome window with the baseUrl. In the terminal a repl is started where you interact with the webpage using protractor/WebDriver selectors and commands. Once you have found the proper selectors and commands
put them in a spec file so are run in CI later.
This works for an Angular app only.


## Run e2e test
If the tests fail in CI, it can be useful to run them locally:
`npm run-script e2e -- --specs tests/<your spec file> --baseUrl <url of your running app>`
This automatically launches a Selenium server (the one installed through the  above setup).

See https://github.com/angular/protractor/blob/master/docs/debugging.md
