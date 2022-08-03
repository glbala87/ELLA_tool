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

The following steps assume the folder structure and config locations:

```
data/
├── analyses/
|  └── imported/  # Analyses that have already been imported                         $ANALYSES_PATH
|  ├── incoming/  # Analyses to be imported automatically by the analysis watcher    $ANALYSES_INCOMING
├── attachments/  # Storage of user attachments                                      $ATTACHMENT_STORAGE
├── fixtures/     # Configuration data to be imported into the database
|  └── genepanels/
|  ├── users.json
|  ├── usergroups.json
|  ├── references.json
|  ├── filterconfigs.json
├── igv-data/     # IGV resources, global and usergroup tracks                       $IGV_DATA
|  ├── tracks/
|  ├── track_config_default.json
├── ella_config.yml                                                                  $ELLA_CONFIG
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

_e.g.,_

```bash
# Listen port for nginx. Default: 3114
# PORT=3114

# URI with PostgreSQL credentials. The user and database must already exist.
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

### Create ELLA application config

Many of the settings can be adjusted as you go, but a basic application config is required for all
additional steps. It must be available inside the container at the value given by `ELLA_CONFIG` in
the env file.

- Documentation
  - [Configuration overview](/technical/configuration.html#application-configuration)
  - [Application configuration](/technical/application.md)
- Example in [alleles/ella-testdata](https://gitlab.com/alleles/ella-testdata)
  - [testdata/example_config.yml](https://gitlab.com/alleles/ella-testdata/-/tree/main/testdata/example_config.yml)

### Using `ella-cli`

The following steps use `ella-cli` from inside the ella container. You can do this by starting a
shell session inside a running container or using an alias/function wrapper to run directly from
the host OS. The latter will make each command take longer, but lets you interact with the host
OS and container in a single terminal.

```bash
ELLA_DIR=$PWD
ELLA_IMAGE=registry.gitlab.com/alleles/ella:v1.16.4
ENV_FILE=prod.env

# start an interactive bash shell
ella-shell() {
  docker run -it --rm \
    --name ella-shell \
  	--env-file "$ENV_FILE" \
  	-v "$ELLA_DIR/data:/data" \
  	-v "$ELLA_DIR/logs:/logs" \
  	-v /tmp \
  	"$ELLA_IMAGE" bash
}

# run a single command in an 
ella-cli() {
  docker run -it --rm \
  	--env-file "$ENV_FILE" \
  	-v "$ELLA_DIR/data:/data" \
  	-v "$ELLA_DIR/logs:/logs" \
  	-v /tmp \
  	"$ELLA_IMAGE" ella-cli "$@"
}
```

### Initializing the database

ELLA relies on an external PostgreSQL database, using the default "public" schema.

Run the following command:

``` bash
ella-cli database make-production
```

This will:

1. Setup the database from the migration base.
2. Run all the migration scripts.
3. Run the `database refresh` command, to setup json schemas and various triggers.

Once this is complete, you can start a persistent ELLA container and it will stay running. Most of
the supervisord processes will fail, but it can make running the next `ella-cli` commands easier.

### Define/Fetch configuration fixtures

ELLA is very configurable and as a result there are several configuration files that need to be
prepared before the database can created and populated. Each file has documentation contain the
details of its contents as well as a sample config available in the test data that can be used as
reference.

In depth info is available in [Configuration](/technical/configuration.md) for all configuration
options.

Some configs rely on each other, so when initially populating the database they must be loaded in
the following order.

#### Gene Panels

Gene panels are a core part of ELLA and must be loaded first.

- Documentation
  - [Gene Panel Configuration](/technical/genepanels.md)
- Examples
  - [testdata/clinicalGenePanels](https://gitlab.com/alleles/ella-testdata/-/tree/main/testdata/clinicalGenePanels)
- Gene Panels used by OUS AMG
  - [alleles/genepanel-store](https://gitlab.com/alleles/genepanel-store)

It is not currently possible to bulk load gene panels, so using a loop is recommended.

```bash
# adjust path to genepanels as needed
for gp_dir in /data/fixtures/genepanels/*/; do
  ella-cli deposit genepanel --folder $gp_dir
done
```

#### User Groups

User groups are used to determine who can see what as well as which filters are available and
used by default.

- Documentation
  - [Users and User Group Configuration](/technical/users.html#user-groups)
- Examples
  - [usergroups.json](https://gitlab.com/alleles/ella-testdata/-/blob/main/testdata/fixtures/usergroups.json)

```bash
ella-cli users add_groups /data/fixtures/usergroups.json
```

#### Filter Configs

In addition to gene panels, ELLA has highly configurable and extendable filters that make ignoring
technical and known-but-uninteresting variants much simpler.

- Documentation
  - [Filter Configuration](/technical/filtering.md)
- Examples
  - [filterconfigs.json](https://gitlab.com/alleles/ella-testdata/-/blob/main/testdata/fixtures/filterconfigs.json)

```bash
ella-cli filterconfigs update /data/fixtures/filterconfigs.json
```

#### Users

Users can be added one by one or as a bulk action. It is currently only possible to add users via
the CLI.

- Documentation
  - [Users and Passwords](/technical/users.html#users-and-passwords)
- Examples
  - [users.json](https://gitlab.com/alleles/ella-testdata/-/blob/main/testdata/fixtures/users.json)

```bash
ella-cli users add_many /data/fixtures/users.json
```

#### Annotation

TODO: normal + configurable annotation

#### IGV

[IGV.js](https://github.com/igvteam/igv.js) is used in [visual mode](/manual/visual.md) for
examining variants in more detail. Its configuration is dynamic, so does not need to be loaded into
the database. The config and any necessary files for the track info must be available in
`$IGV_DATA`/`$IGV_DATA/tracks` and have the correct permissions.

- Documentation:
  - [UI Options: IGV](/technical/uioptions.html#igv-and-tracks-in-visual)
- Example:
  - [igv-data](https://gitlab.com/alleles/ella-testdata/-/tree/main/testdata/igv-data)

```bash
# Download the default IGV data
ella-cli igv-download "$IGV_DATA"

# If running ELLA in an airgapped network, you can download the files directly for a manual
# transfer afterwarads. This does not need to be run inside an ELLA container.
mkdir igv-data
./src/cli/commands/fetch-igv-data.sh igv-data
tar cvf igv_data.tar igv-data/
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

1. If you haven't already, start the ELLA container
2. Verify the container is running
   ```bash
   # from the host
   docker ps --filter=name=ella-prod
   # CONTAINER ID   IMAGE                                      COMMAND                  CREATED         STATUS         PORTS     NAMES
   # e475a3c0068b   registry.gitlab.com/alleles/ella:v1.16.4   "/ella/ops/prod/entr…"   2 minutes ago   Up 2 minutes             ella-prod
   ```
3. Check the status of supervisord processes. If you started the container after first initializing
   the database, they will be failed and need to be started again.
   ```bash
   # inside the container
   supervisorctl -c /ella/ops/prod/supervisor.cfg status
   # analysis-watcher                 RUNNING   pid 42, uptime 0:05:10
   # api                              RUNNING   pid 43, uptime 0:05:10
   # nginx                            RUNNING   pid 44, uptime 0:05:10
   # polling                          RUNNING   pid 45, uptime 0:05:10
   ```
4. If any processes have exited, start them up again
   ```bash
   supervisorctl -c /ella/ops/prod/supervisor.cfg start all
   supervisorctl -c /ella/ops/prod/supervisor.cfg status
   # analysis-watcher                 RUNNING   pid 42, uptime 0:00:07
   # ...
   ```
   - if any of the processes still fail to start, check the logs to determine the cause.
5. Go to the appropriate URL/port and log in.
6. Success!
