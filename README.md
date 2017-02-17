ella is a web app based on AngularJS with a Flask REST backend.

Most functionality is now baked into a Makefile, run `make help` to see a quick overview of available commands.

# Deployment

## Production

Only requirement for production deployment is an existing PostgresSQL database.

ella uses docker for deployment, making it as easy as running two commands.

First build the docker image as follows:

```
docker build -t {image_name} .
```

where `{image_name}` is what you want to call the image.

Next, launch a new container with

```
docker run --name {container_name} -p 80:80 -v /path/to/repo:/repo -v /path/to/logs:/logs -e DB_URL={db_url} {image_name}
```

Internally, the container will spin up nginx, several API workers, transpile the frontend and launch the analyses watcher.

Transpiling the frontend files may take up to a minute, so it might take some time before the application is available.

The repo looks like the following:

```

/repo/
  /incoming/
    Analysis-2/
      Analysis-2-Genepanel_v01.vcf
      Analysis-2-Genepanel_v01analysis
      Analysis-2.bam
      Analysis-2.bai
      Analysis-2.sample
  /imported/
    Analysis-1/
      Analysis-1-Genepanel_v01.vcf
      Analysis-1-Genepanel_v01analysis
      Analysis-1.bam
      Analysis-1.bai
      Analysis-1.sample
  /genepanels/
    Genepanel_v01/
      Genepanel_v01.transcripts.csv
      Genepanel_v01.phenotypes.csv

```

Analyses in `incoming/` will be automatically imported and placed into `imported/`.
`genepanels/` is similarily watched for new genepanels, and any new genepanels will be imported automatically.

## Demo

To spin up a new demo instance, run the following:

```
make build
DEMO_NAME=domain.com make demo
```

`DEMO_NAME` will add the corresponding host to VIRTUAL_HOST inside the container, for use with nginx-proxy docker container.

If you want to bind the demo directly to the local host you can instead run it manually like this:

```
docker run -d \
		--name {container_name} \
		-p 80:80 \
		{image_name} \
		supervisord -c /ella/ops/demo/supervisor.cfg

docker exec {container_name} make dbreset
```

The demo container runs an internal PostgreSQL server for easier deployment.

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
1. Make and enter a dev instance: `make dev` and `make shell`
1. Inside it do:
    1. `export DB_URL=postgresql:///postgres`
    1. `/ella/ella-cli database ci-migration-head` (resets database to the migration base, then runs all the migrations)
    1. `cd /ella/src/vardb/datamodel/migration/`
    1. `PYTHONPATH=../../.. alembic revision --autogenerate -m "Name of migration"`. This will look at the current datamodel
     and compare it against the database state, generating a migration script from the differences.
1. Go over the created script, clean it up and test it (`test-api-migration`).

The migration scripts are far from perfect, so you need some knowledge of SQLAlchemy and Postgres to get it right. Known issues are `Sequences` and `ENUM`s, which have to be taken care of manually. Also remember to convert any data present in the database if necessary.
The `test-api-migration` part of the test suite will test also test database migrations, by running the api tests on a migrated database.


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

# End to end testing (e2e)
We use webdriver.io for testing. See http://webdriver.io.

In CI tests are run with `make e2e-test`. This will run Chrome in it's own container and run the test suites.
You can run this locally to check that the tests are passing, but it's unsuitable for authoring/editing tests.

To explore the e2e test data, start a local Ella instance and import the e2e test data: `.../reset?testset=e2e`


## Local usage, REPL and debugging
- Download and install chromedriver and Chrome/Chromium.
- Run `./chromedriver  --port=4444 --whitelisted-ips= --url-base ''` on your local machine.
- Run `make e2e-test-local`. You'll be presented with a shell inside the container.
- Run `make wdio APP_BASE_URL=.. CHROME_HOST=..` inside the shell to start the tests. It will connect to the locally running chromedriver (given by CHROME_HOST as IP address) and test the app that runs on APP_BASE_URL (ip:port).
  To run only a specific test, add WDIO_OPTIONS='--spec <path to test>'
Maximize the Chrome window to reduce the number of 'element-not-clickable' errors.

To install chromedriver:
- brew info chromedriver
- or https://sites.google.com/a/chromium.org/chromedriver/downloads

Best way to get and test selectors in Chrome is to use the `CSS Selector Helper for Chrome` extension.
Another way is to use the search (`Ctrl+F`) functionality in the Developer Tools to test your selector.

You can connect a debugger to Node.js instance on port `5859` to play around.

Use `browser.debug()` in a test file to pause the execution of the tests. It will present a REPL (webdriverio >= 4.5.0) where can you interact with webdriverio client to try out various commands, like `browser.element(...)`. It's also useful to head over to the browser's console to experiment and inspect variables.
Hit 'Ctrl-c' in the REPL to continue the test run. See more on http://webdriver.io/guide/usage/repl.html

More info at http://webdriver.io/guide/testrunner/debugging.html