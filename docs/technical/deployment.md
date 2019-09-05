# Deployment

::: danger NOTE
ELLA should not run on an network with public access, but rather in a walled garden, with restricted external access.
:::

## Production

Only requirement for production deployment is an existing PostgresSQL database.

ELLA primarily uses Docker for deployment. Not using Docker is also possible, but is not documented.

### Build image

First build the docker image as follows:

```
docker build -t {image_name} .
```

where `{image_name}` is what you want to name the image.

### Mount points

The production container defines a few mount points.
If you're not using containers for deployment, you can skip this section.

| Destination	| Description  	                          |
|------------	|----------------------	                  |
| /logs/      | Destination for the log files           |
| /data/      | Data files           	                  |
| /socket/    | Location for unix sockets (optional)    |
| /tmp/       | Location for temporary files (optional) |


### Data directory

The recommended approach is to have one data directory for ELLA, which contains imported analyses, attachments and IGV data. This directory is outside of the container, and can be mounted in to /data.

One possible structure is this:

```
/data/
  attachments/ - Storage of user attachments
  analyses/
    incoming/  - New analyses for analysis watcher
    imported/  - Analyses that are imported
  igv-data/    - IGV resources, global and usergroup tracks.
  fixtures/    - Any kind of data that is imported into database. Examples:
    users.json
    usergroups.json
    references.json
    filterconfigs.json
    genepanels/

```

### Setup environment

There are a few environment variables that should be set.

| Variable  	    | Description  	                                 | Values  |
|------------	    | ---------------------------------------------- | ------  |
| DB_URL    | URI to PostgreSQL database.	                         | ex. postgresql://dbuser@host/dbname   |
| PORT      | Listen port for nginx.	                         | Default: 3114   |
| ANALYSES_PATH   | Path to imported analyses. 	| path, ex. /data/analyses/imported |
| ANALYSES_INCOMING   | Path to incoming analyses. Used by analysis watcher to import new analyses 	| path, ex. /data/analyses/incoming |
| IGV_DATA   | Path to IGV resources. 	| path, ex. /data/igv_data |
| ATTACHMENT_STORAGE   | Path to where to store attachments. 	| path, ex. /data/attachments/ |
| ANNOTATION_SERVICE_URL   | URL to `anno` service. 	| URL, ex. "http://localhost:6000" |
| OFFLINE_MODE    | Whether used in offline environment. Adjusts whether links should be copied to clipboard.	| TRUE/FALSE (default: FALSE )    |


### Start container

We can launch a new container like the following

```
docker run \
  --name {container_name} \
  -p 80:80 \
  -v /local/logs/path:/logs \
  -v /local/logs/path:/logs \
  -e DB_URL={db_url} \
  -e ANALYSES_PATH=/data/analyses/imported \
  -e ANALYSES_INCOMING=/data/analyses/incoming \
  -e ATTACHMENT_STORAGE=/data/attachments \
  -e IGV_DATA=/data/igv_data \
  -e ANNOTATION_SERVICE_URL=http://localhost:6000 \
  {image_name}
```

The default entrypoint is `ops/prod/entrypoint.sh`, which will in turn start Supervisor to manage the different processes.

### Behind the scenes

Internally, the `supervisord` will spin up several services:

  - nginx - acting as reverse proxy and serving static files
  - gunicorn - launching several API workers
  - analyses-watcher - handles watching for and importing new analyses
  - polling - watches for and handles new import jobs


### Creating the production database

ELLA relies on an external PostgreSQL database, using the default 'public' schema.
Provide the URI to the database using the DB_URL environment variable.

Run the following command:

`ella-cli database make-production`

This will first setup the database from the migration base, then run all the migration scripts. Last it will run the `database refresh` command, to setup json schemas and various triggers.
