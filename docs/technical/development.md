# Development

## Getting started
- Start a development environment in Docker, run **`make dev`** - you may need to do `make build` first
- Populate the database by running `make db` or `make db TEST_SET=..`
 if you want something else than the default data. See vardb/deposit/deposit_testdata.py#AVAILABLE_TESTSETS

To get visibility into what's happening in the browser client, start the Cerebral debugger (<https://cerebraljs.com/docs/introduction/debugger.html>).
Enter any name ('ella' is a good name) and port 8585. This sets up a server listening on that part port.
Open the app in the browser (refresh if the app was openen before starting Cerebral). The browser will connect
to the Cerebral. Make sure the server port match the port configured in webui/src/js/index.js


## Ops

Bringing up the production/development/demo/testing systems are handled by `Make` and `supervisord`.
Look in `Makefile` and in  `ops/` for more information.

## Migration
Whenever you make changes to the database model, you need to create migration scripts, so that the production database
can be upgraded to the new version. We use Alembic to assist creating those scripts. Migration scripts are stored in
`src/vardb/datamodel/migration/alembic/`. The current migration base is stored in `src/vardb/datamodel/migration/ci_migration_base`.
This base serves as the base for which the migration scripts will be built against, and should represent the oldest
database in production.

### Create a new migration

1. Make all your changes to the normal datamodel in `src/vardb/datamodel/` and test them until you're satisfied.
   In general we don't want to make more migration scripts than necessary, so make sure things are proper.
1. Make and enter a dev instance: `make dev` and `make shell`
1. Inside it do:
    1. `/ella/ella-cli database ci-migration-head` (resets database to the migration base, then runs all the migrations)
    1. `cd /ella/src/vardb/datamodel/migration/`
    1. `PYTHONPATH=../../.. alembic revision --autogenerate -m "Name of migration"`. This will look at the current datamodel
     and compare it against the database state, generating a migration script from the differences.
1. Go over the created script, clean it up and test it (`test-api-migration`).

The migration scripts are far from perfect, so you need some knowledge of SQLAlchemy and Postgres to get it right.
Known issues are `Sequences` and `ENUM`s, which have to be taken care of manually. Also remember to convert any data
present in the database if necessary.

The `test-api-migration` part of the test suite will test also test database migrations, by running the api tests on a migrated database.

### Manually testing the migrations
To manually test the migration scripts you can run the upgrade/downgrade parts of the various migrations:
- $ ./ella-cli database ci-migration-base [0/1556]
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

You can explore the *ella*'s API at `/api/v1/docs/` in you browser.

To document your resource, have a look at the current resources to see usage examples.

Under the hood, the resources and definitions (models) are loaded into `apispec` in `api/v1/docs.py`. The spec is made available at `/api/v1/specs/`.
The definitions are generated automatically by `apispec` using it's Marshmallow plugin.