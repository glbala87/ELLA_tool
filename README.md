ella is a web app based on AngularJS with a Flask REST backend.

Most functionality is now baked into a Makefile, run `make help` to see a quick overview of available commands.

# Documentation
More info about the app can be found in the docs folder.
The docs is written in Markdown and compiled using GitBook. See https://toolchain.gitbook.com/ for more info.

The create a web-based view of the doc:
- install GitBook: `npm install gitbook-cli -g`
- `cd docs; gitbook serve`

To create diagrams of the datamodel, run `make diagrams`. The diagrams is created inside a container and streamed
to a local file PNG file.

## Release
Some info about tagging, building release artefacts and making release notes.


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

Mount points of interest:
  - `/logs` - application logs
  - `/repo` - repository of analyses/genepanels. See below


Internally, the `supervisord` will spin up:
  - nginx - acting as reverse proxy and serving static files
  - gunicorn - launching several API workers
  - gulp - transpiles the frontend upon startup
  - analyses-watcher - handles watching for and importing new data

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
DEMO_NAME=domain.com make demo
```

Inside the container an environment variable VIRTUAL_HOST will be set equal to the value `DEMO_NAME` for use with the nginx-proxy docker container.


If you want to bind the demo directly to the local host you can instead run it manually like this:

```
docker run -d \
		--name {container_name} \
		-p 80:80 \
		{image_name} \
		supervisord -c /ella/ops/demo/supervisor.cfg

# when the processes inside the container have started up, populate the database:
docker exec {container_name} make dbreset
```

The demo container runs an internal PostgreSQL server for easier deployment.

# Development

### Getting started:
- Start a development environment in Docker, run **`make dev`** - you may need to do `make build` first
- Populate the database by running `make db` or `make db TEST_SET=..`
 if you want something else than the default data. See vardb/deposit/deposit_testdata.py#AVAILABLE_TESTSETS

To get visibility into what's happening in the browser client, start the Cerebral debugger (https://cerebraljs.com/docs/introduction/debugger.html).
Enter any name ('Ella' is a good name) and port 8585. This sets up a server listening on that part port.
Open the app in the browser (refresh if the app was openen before starting Cerebral). The browser will connect
to the Cerebral. Make sure the server port match the port configured in webui/src/js/index.js


### Ops

Bringing up the production/development/demo/testing systems are handled by `Make` and `supervisord`.
Look in `Makefile` and in  `ops/` for more information.

### Migration:
Whenever you make changes to the database model, you need to create migration scripts, so that the production database
can be upgraded to the new version. We use Alembic to assist creating those scripts. Migration scripts are stored in
`src/vardb/datamodel/migration/alembic/`. The current migration base is stored in `src/vardb/datamodel/migration/ci_migration_base`.
This base serves as the base for which the migration scripts will be built against, and should represent the oldest
database in production.

#### Create a new migration

1. Make all your changes to the normal datamodel in `src/vardb/datamodel/` and test them until you're satisfied.
   In general we don't want to make more migration scripts than necessary, so make sure things are proper.
1. Make and enter a dev instance: `make dev` and `make shell`
1. Inside it do:
    1. `export DB_URL=postgresql:///postgres`
    1. `/ella/ella-cli database ci-migration-head` (resets database to the migration base, then runs all the migrations)
    1. `cd /ella/src/vardb/datamodel/migration/`
    1. `PYTHONPATH=../../.. alembic revision --autogenerate -m "Name of migration"`. This will look at the current datamodel
     and compare it against the database state, generating a migration script from the differences.
1. Go over the created script, clean it up and test it (`test-api-migration`).

The migration scripts are far from perfect, so you need some knowledge of SQLAlchemy and Postgres to get it right.
Known issues are `Sequences` and `ENUM`s, which have to be taken care of manually. Also remember to convert any data
present in the database if necessary.

The `test-api-migration` part of the test suite will test also test database migrations, by running the api tests on a migrated database.

#### Manually testing the migrations
To manually test the migration scripts you can run the upgrade/downgrade parts of the various migrations:
- $ ./ella-cli database ci-migration-base                                                                                                                                                           [0/1556]
- $ ./ella-cli database upgrade e371dfeb38c1
- $ ./ella-cli database upgrade 94a80b8848df
- $ ./ella-cli database downgrade e371dfeb38c1

For migrations involving user generated data, it would be useful to run the migrations (both upgrade and downgrade)
with the database populated through "real" use.

Typically you call the `/reset` endpoint and then interact with the application through the GUI.
The `reset` won't create the alembic table and the upgrade/downgrade scripts will fail.

So before manually running the upgrade/downgrade scripts, you need to create the alembic table:
```
 create table alembic_version (version_num varchar)
```

## Configuration relevant for variant filtering and the ACMG rules engine
Values that affect variant filtering and the rules engine are defined at three levels, in order from general to specific:
- global (defined in code: api/config.py)
- genepanel (common for all genes in the panel)
- genepanel (specific for a single gene. Multiple genes must be configured individually)

The genepanel configuration are part of the genepanel, and values are loaded from a json file. Schema file(s)
in src/vardb/datamodel defines the format of the file.

Configuration at a specific level "override" the more general ones.

Frequency values in global or genepanel common are defined with one set for AD genes, and another for non-AD genes.
For frequencies defined at the gene level, it's not relevant to distingiush between AD/non-AD, as this is defined by the
phenotypes of the gene as defined in the genepanel.

At genepanel common/gene level one can choose to override internal or external, and either AD and non-AD blocks.

### global config
See api/config.py at key 'variant_criteria' > 'genepanel_config':
- freq_cutoff_groups
  - AD
    - internal
    - external
  - default
    - internal
    - external
- disease_mode
- last_exon_important

### genepanel (common) at key 'data'
- freq_cutoff_groups
  - AD
    - internal
    - external
  - default
    - internal
    - external
- disease_mode
- last_exon_important

### genepanel (gene specific) at key 'data'
- genes
  - BRCA1
    - freq_cutoffs
      - internal
      - external
    - disease_mode
    - last_exon_important
  - ...


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
- `make test` will run most test types apart from e2e.
- `make test-{type}` will run the different types of test.

## Specific test

If you want to run a specific API test while developing, you can enter the docker container and run `source /ella/ops/dev/setup-local-integration-test.source`. This script will tell the test framework to use your local database dump after the initial run, saving you a lot of time when running the test again.

# End to end testing (e2e)
We use webdriver.io for testing. See http://webdriver.io.

In CI tests are run with `make e2e-test`. This will run Chrome in it's own container and run the test suites.
You can run this locally to check that the tests are passing, but it's unsuitable for authoring/editing tests.

To explore the e2e test data, start a local Ella instance and import the e2e test data: `.../reset?testset=e2e`


## Local usage, REPL and debugging
The following must be installed:
- Chrome
- Chromedriver

The ELLA app and the test execution (wdio) can be either run locally on your host machine or inside Docker.

First start chromedriver on your host machine: `./chromedriver  --port=4444 --whitelisted-ips= --url-base ''`

Then start the tests: `make e2e-test-local ..options..`

It will connect to the locally running Chromedriver and run one or several test specs.
You'll see a local chrome browser where a "ghost" will click and enter text.

You can put debug statements  (browser.debug())in your test spec to have the test execution stop and enter a REPL to interact with the
browser. You can also open the dev tools in Chrome to dig around. Exit the REPL to have the test continue.

The relevant options to the make command:
- DEBUG=true (Will make the browser visible (as opposed to headless), and increase test timeouts)
- CHROME_HOST=.. the IP address where chromedriver is running. This will start a Chrome browser.
- Add SPEC="<path to test>" to run only a single/few tests. They must given as src/webui/tests/e2e/tests/.. (comma separated if multiple).
- APP_URL: url of the app to test, like http://localhost:8001. Make sure to use an ip/port that is accessible from within the container where the tests themselves are running.
  If not defined the app running inside container of the test execution is used.

Maximize the Chrome window to reduce the number of 'element-not-clickable' errors.

Note! Make sure the versions of Chrome and Chromedriver are compatible


Note! You can also run webdriverio directly on hour host (not in a docker container).
- Start ELLA (typically `make dev`)
- Start tests: DEBUG=true node node_modules/.bin/wdio src/webui/tests/e2e/wdio.conf.js --path / --baseUrl <host:port like localhost:8001>

Maximize the Chrome window to reduce the number of 'element-not-clickable' errors.
Of course you need to have instellad the webdriverio Node module.

### Installing

Chromedriver:
- brew info chromedriver
- or https://sites.google.com/a/chromium.org/chromedriver/downloads

### Misc

Best way to get and test selectors in Chrome is to use the `CSS Selector Helper for Chrome` extension.
Another way is to use the search (`Ctrl+F`) functionality in the Developer Tools to test your selector.

You can connect a debugger to Node.js instance on port `5859` to play around.

Use `browser.debug()` in a test file to pause the execution of the tests. It will present a REPL (webdriverio >= 4.5.0) where can you interact with webdriverio client to try out various commands, like `browser.element(...)`. It's also useful to head over to the browser's console to experiment and inspect variables.
Hit 'Ctrl-c' in the REPL to continue the test run. See more on http://webdriver.io/guide/usage/repl.html

More info at http://webdriver.io/guide/testrunner/debugging.html
