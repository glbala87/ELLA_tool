# Production

::: warning NOTE
This documentation is a work in progress and may be incomplete.
:::

::: danger WARNING
This guide does not include setting up SSL. For proper security, ELLA should either be run in a
secured environment (internal network, *"walled garden"*, etc.) or with the nginx config modified
to handle remote connections securely.
:::

::: danger WARNING
ELLA relies on a separate annotation service, [ella-anno](https://gitlab.com/alleles/ella-anno), to annotate and import data.
The [documentation for this service](http://allel.es/anno-docs) is also a work in progress. Please contact
[ella-support](ma&#105;lt&#111;&#58;&#101;%6&#67;la&#37;2&#68;s&#117;pport&#64;m&#101;&#100;i&#115;&#105;&#110;&#46;%75i%&#54;F&#46;n%&#54;F)
for details on how to configure it for your own production setup. A sample docker-compose stack is
(or will eventually be) available at [alleles/demo](https://gitlab.com/alleles/demo).
:::

[[toc]]


## Requirements

- [PostgreSQL](https://www.postgresql.org/)
  - Minimum: &ge; v9.6
  - Recommended: &ge; v11.4
- [Docker](https://www.docker.com/)
  - Some steps also include info for using [Singularity](https://sylabs.io/) rather than Docker,
    but may not be as comprehensive.
  - Running ELLA outside of a container is also possible, but is not documented (or recommended).

## Background

### Using `ella-cli`

Some of the following steps require or are made simpler by using `ella-cli`. To function properly
it requires the same environment as the ELLA application. It is recommended to use the 

### Mount points

There are several directories you will want to mount from the host OS into the container.

| Destination | Description                                             |
| ----------- | ------------------------------------------------------- |
| `/data`     | Data files (details below)                              |
| `/logs`     | API / supervisor log files                              |
| `/tmp`      | Using host `/tmp` can increase performance _(optional)_ |


### Data directory

ELLA needs access to various types of data, and while it is possible to mount those all individually,
using a single unified `/data` directory is _strongly_ recommended for both clarity and simplicity.

Recommended folder structure:

```
data/
├── attachments/  # Storage of user attachments
├── analyses/
|  ├── incoming/  # Analyses to be imported automatically by the analysis watcher
|  └── imported/  # Analyses that have already been imported
├── igv-data/     # IGV resources, global and usergroup tracks.
├── fixtures/     # Configuration data to be imported into the database
|  ├── users.json
|  ├── usergroups.json
|  ├── references.json
|  ├── filterconfigs.json
|  └── genepanels/
```

### Supervisor

The default entrypoint is `ops/prod/entrypoint.sh`, which uses Supervisor to manage several
processes.

  - _nginx_ - reverse proxy for the gunicorn workers and serves static files
  - _gunicorn_ - API / worker processes
  - _analyses-watcher_ - monitors `$ANALYSES_INCOMING` to import new analyses as they come in and
    then moves them to `$ANALYSES_PATH`
  - _polling_ - interfaces with the annotation service and imports data for samples sent for
    reanalysis

## First time setup

The [ELLA release page](https://gitlab.com/alleles/ella/-/releases) has information on past and
current releases, including the Docker and Singularity images. This information can also be quickly
gathered by running `make latest-release-info`.

### Fetching the release image

Determine the latest Docker and Singularity image by whichever method you prefer, and then pull
them to the local server.

```bash
# Docker
docker pull registry.gitlab.com/alleles/ella:${TAG}

# Singularity - download
wget https://gitlab.com/alleles/ella/-/releases/${TAG}/downloads/ella-release-${TAG}.sif

# Singularity - build from Docker
singularity pull docker://registry.gitlab.com/alleles/ella:${TAG}
```


### Define the environment

There are a few environment variables that should be set, and many others than can be modified to
fit the production environment. In the following steps, it is assumed they are in an env file.


An example env file is:

```bash
# Listen port for nginx. Default: 3114
# PORT=3114

# URI with PostgreSQL credentials
DB_URL=postgresql://dbuser@host/dbname

# Application configuration
ELLA_CONFIG=/data/ella_config.yml

# Path used by the watcher for auto-importing new analyses
ANALYSES_INCOMING=/data/analyses/incoming

# Path to analyses that have already been imported
ANALYSES_PATH=/data/analyses/imported

# Path to IGV resources
IGV_DATA=/data/igv_data
```

See [Application Configuration](/technical/application.md) for all variables related to the setup
of ELLA application.

Check the relevant
[Docker](https://docs.docker.com/engine/reference/commandline/run/#set-environment-variables--e---env---env-file)
and/or
[Singularity](https://docs.sylabs.io/guides/3.10/user-guide/environment_and_metadata.html#environment-from-the-host)
documentation for other ways of passing this information to the container.

### Define/Fetch configuration fixtures

ELLA is very configurable and as a result there are several configuration files that need to be prepared before
the database can created and populated. Each file has documentation contain the details of its contents as well
as a sample config available in the test data that can be used as reference.

In depth info is available in [Configuration](/technical/configuration.md) for all configuration options.

#### IGV

TODO

[IGV.js](https://github.com/igvteam/igv.js) is used in [visual mode](/manual/visual.md) for examining variants
in more detail. 

  - `ella-cli igv-download`

#### Gene Panels

TODO

- error message on bad genepanel folder sucks
- add `--all` flag?
- can only deposit one by one

#### User Groups

TODO

#### Filter Configs

TODO

#### Users

TODO

### Create the production database

ELLA relies on an external PostgreSQL database, using the default "public" schema.

Provide the URI to the database using the `DB_URL` environment variable.

Run the following command:

``` bash
ella-cli database make-production
```

This will:
1. Setup the database from the migration base.
2. Run all the migration scripts.
3. Run the `database refresh` command, to setup json schemas and various triggers.

### Load configuration files

TODO

```bash
ella-cli blah blah blah
```

### Populate reference table

The references table in the database can be populated with PubMed IDs using a json file generated by the ella-cli:

1. Gather all the PubMed IDs you want to populate the database with in a line-separated file.
2. Run this command to create a file named references-YYMMDD.json:<br>
    ``` bash
    ella-cli references fetch <path to file with PubMed ids>
    ```
3. Create or update references in the database with this command:<br>
    ``` bash
    ella-cli deposit references <path to references-YYMMDD.json>
    ```

### Log in / verify

TODO
