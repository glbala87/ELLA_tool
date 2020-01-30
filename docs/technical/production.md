# Production

::: warning NOTE
This documentation is a work in progress and is incomplete.

Please contact developers for more details.
:::

::: danger WARNING
For proper security, ELLA should be run in a walled garden with restricted external access, rather than on a public network.  
:::

::: danger WARNING
ELLA relies on a separate annotation service to annotate and import data. Our own service, `ella-anno`, is currently only available in our internal GitLab repository, due to large size of the annotation sources (about 30 GB). We are working on making the repository public (with artifacts in the cloud) in the near future, along with proper documentation and a simpler procedure for deployment together with ELLA. Until then, please contact <u>[ella-support](ma&#105;lt&#111;&#58;&#101;%6&#67;la&#37;2&#68;s&#117;pport&#64;m&#101;&#100;i&#115;&#105;&#110;&#46;%75i%&#54;F&#46;n%&#54;F)</u> for details on how to configure your own production setup.
:::

## Requirements

- A [PostgreSQL](https://www.postgresql.org/) database. Minimum required version is 9.6, but we recommend version 11.4 or higher.
- ELLA primarily uses [Docker](https://www.docker.com/) for deployment. Other alternatives (e.g. using [Singularity](https://sylabs.io/) or no container) is also possible, but is not documented here.


## Build image

First build the docker image:

```
docker build -t {image_name} .
```

where `{image_name}` is what you want to name the image.

## Mount points

The production container defines a few mount points. If you're not using containers for deployment, you can skip this section.

| Destination	| Description  	                          |
|------------	|----------------------	                  |
| /logs/      | Destination for the log files           |
| /data/      | Data files           	                  |
| /socket/    | Location for unix sockets (optional)    |
| /tmp/       | Location for temporary files (optional) |


## Data directory

The recommended approach is to have one data directory for ELLA, which contains imported analyses, attachments and IGV data. This directory is outside of the container, and can be mounted in to /data.

Example folder structure:

```
/data/
  attachments/ - Storage of user attachments
  analyses/
    incoming/  - New analyses for analysis watcher
    imported/  - Analyses that are imported
  igv-data/    - IGV resources, global and usergroup tracks.
  fixtures/    - Any kind of configuration data that should be imported into the database. Examples:
    users.json
    usergroups.json
    references.json
    filterconfigs.json
    genepanels/

```

## Setup environment

There are a few environment variables that should be set:

| Variable  	    | Description  	                                 | Values  |
|:--- | :---  | :---  |
| `DB_URL`    | URI to PostgreSQL database.	                         | (e.g. `postgresql://dbuser@host/dbname`)   |
| `PORT`     | Listen port for nginx.	                         | Default: `3114`  |
| `ANALYSES_PATH`  | Path to imported analyses. 	| path (e.g. `/data/analyses/imported`) |
| `ANALYSES_INCOMING`   | Path to incoming analyses. Used by analysis watcher to import new analyses 	| path (e.g. `/data/analyses/incoming`) |
| `ELLA_CONFIG`  | Application configuration. 	| path (e.g. `/config/ella_config.yml`) |
| `IGV_DATA`  | Path to IGV resources. 	| path (e.g. `/data/igv_data`) |

Additional environment variables can be utilized in the [Application configuration](/technical/application.md).

## Start container

We can launch a new container like the following

```
docker run \
  --name {container_name} \
  -p 80:80 \
  -v /local/data/path:/data \
  -v /local/config/path:/config \
  -v /local/logs/path:/logs \
  -e ELLA_CONFIG=/config/ella_config.yml \
  -e DB_URL={db_url} \
  -e ANALYSES_PATH=/data/analyses/imported \
  -e ANALYSES_INCOMING=/data/analyses/incoming \
  -e IGV_DATA=/data/igv_data \
  {image_name}
```

The default entrypoint is `ops/prod/entrypoint.sh`, which will in turn start Supervisor to manage the different processes.

## Behind the scenes

Internally, the `supervisord` will spin up several services:

  - nginx - acting as reverse proxy and serving static files
  - gunicorn - launching several API workers
  - analyses-watcher - handles watching for and importing new analyses
  - polling - watches for and handles new import jobs


## Creating the production database

ELLA relies on an external PostgreSQL database, using the default "public" schema. 

Provide the URI to the database using the `DB_URL` environment variable.

Run the following command:

```
ella-cli database make-production
```

This will: 
1. Setup the database from the migration base.
2. Run all the migration scripts. 
3. Run the `database refresh` command, to setup json schemas and various triggers.


## Populate reference table

The references table in the database can be populated with PubMed IDs using a json file generated by the ella-cli: 

1. Gather all the PubMed IDs you want to populate the database with in a line-separated file.
2. Run this command to create a file named references-YYMMDD.json:<br>
    ```
    ella-cli references fetch <path to file with PubMed ids>
    ```
3. Create or update references in the database with this command:<br>
    ```
    ella-cli deposit references <path to references-YYMMDD.json>
    ```

## Configure ELLA

See [Application configuration](/technical/application.md) for settings related to setup of the ELLA application, as well as [Configuration](/technical/configuration.md) for other options.