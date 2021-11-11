# Development

[[toc]]

## Getting started

The recommended way of developing with ELLA is to use VSCode with development containers. For this to work you need to follow the recipe provided [here](https://code.visualstudio.com/docs/remote/containers).

Once VSCode is set up, open the root folder (`ella`) in VSCode, and use the command palette to launch `Remote-Containers: Rebuild and Reopen in Container`*. This will start up a Docker container with ELLA running inside it, and attach VSCode to it. From there, you can populate the database:

Run the task `reset db`.
If you want something other than the data for the e2e test, run `make dbreset` (or `make dbreset TESTSET=default`) in the integrated terminal. See vardb/deposit/deposit_testdata.py#AVAILABLE_TESTSETS.

Now, ELLA should be available on http://localhost:5000, and one can log in with credentials `testuser1:demo`, `testuser2:demo`,...,`testuser8:demo`. The environments for the test users are slightly different.

To get visibility into what's happening in the browser client, start the [Cerebral debugger](https://cerebraljs.com/docs/introduction/devtools.html).
Enter any name ('ella' is a good name) and port 8585. This sets up a server listening on that part port.
Open the app in the browser (refresh if the app was opened before starting Cerebral). The browser will connect
to the Cerebral debugger. To enable the web client to connect to the cerebral debugger, you need to comment out this line
in `./src/webui/src/js/index.js` :

```javascript
// comment out this line
// config.devtools = null
```

Also make sure the server port match the port configured in `webui/src/js/index.js`.

\* On subsequent runs, it is sufficient to run `Remote-Containers: Reopen in Container`


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
1. Make and enter a dev instance (not necessary if inside a devcontainer): `make dev` and `make shell`
1. Inside it do:
    1. `ella-cli database ci-migration-head` (resets database to the migration base, then runs all the migrations)
    1. `cd /ella/src/vardb/datamodel/migration/`
    1. `PYTHONPATH=../../.. alembic revision --autogenerate -m "Name of migration"`. This will look at the current datamodel and compare it against the database state, generating a migration script from the differences.
1. Go over the created script, clean it up and test it (`test-api-migration`).

The migration scripts are far from perfect, so you need some knowledge of SQLAlchemy and Postgres to get it right.
Known issues are `Sequences` and `ENUM`s, which have to be taken care of manually. Also remember to convert any data
present in the database if necessary.

The `test-api-migration` part of the test suite will also test database migrations, by running the api tests on a migrated database.

### Manually testing the migrations

To manually test the migration scripts you can run the upgrade/downgrade parts of the various migrations:
- $ ella-cli database ci-migration-base
- $ ella-cli database upgrade e371dfeb38c1
- $ ella-cli database upgrade 94a80b8848df
- $ ella-cli database downgrade e371dfeb38c1

For migrations involving user generated data, it would be useful to run the migrations (both upgrade and downgrade)
with the database populated through "real" use.

Typically you call `make dbreset` then interact with the application through the GUI.
`dbreset` won't create the alembic table and the upgrade/downgrade scripts will fail.

So before manually running the upgrade/downgrade scripts, you need to create the alembic table and populate it with the corresponding version (`[hash]` is the database `Revision ID`):
```
 CREATE TABLE alembic_version (version_num varchar)
 INSERT INTO alembic_version VALUES ([hash])
```
### Integrating the a new migration step

Once you are satisfied that the newly created migration script does its job, you can add it to the repository.


## API documentation

The API is documented using [apidocs](https://apispec.readthedocs.io/en/latest/) supporting the OpenAPI specification (f.k.a. Swagger 2.0).
You can see the specification [here](http://swagger.io/specification/).

You can explore the ELLA's API at `/api/v1/docs/` in you browser.

To document your resource, have a look at the current resources to see usage examples.

Under the hood, the resources and definitions (models) are loaded into `apispec` in `api/v1/docs.py`. The spec is made available at `/api/v1/specs/`.
The definitions are generated automatically by `apispec` using it's Marshmallow plugin.
