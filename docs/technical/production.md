# Production

::: warning NOTE
This documentation is a work in progress and is incomplete.

Please contact developers for more details.
:::

::: danger WARNING
For proper security, ELLA should be run in a walled garden with restricted external access, rather than on a public network.
:::

::: danger WARNING
ELLA relies on a separate annotation service, [ella-anno](https://gitlab.com/alleles/ella-anno), to annotate and import data. The [documentation for this service](http://allel.es/anno-docs) is work in progress, please contact [ella-support](ma&#105;lt&#111;&#58;&#101;%6&#67;la&#37;2&#68;s&#117;pport&#64;m&#101;&#100;i&#115;&#105;&#110;&#46;%75i%&#54;F&#46;n%&#54;F) for details on how to configure your own production setup.
:::

[[toc]]

## Requirements

- A [PostgreSQL](https://www.postgresql.org/) database. Minimum required version is 9.6, but we recommend version 11.4 or higher.
- ELLA primarily uses [Docker](https://www.docker.com/) for deployment. Other alternatives (e.g. using [Singularity](https://sylabs.io/) or no container) is also possible, but is not documented here.


## Fetch or build container image

Using the tagged released images is recommended, however you can build them locally if preferred.

### Fetching a release image

Check the [ELLA release page](https://gitlab.com/alleles/ella/-/releases) to see info on the latest release.

#### Docker

Pull the Docker image using the tag from the most recent release (_e.g.,_ `v1.16.4`).

```shell
docker pull registry.gitlab.com/alleles/ella:${TAG}
```

#### Singularity

A link to the Singularity image (built directly from the Docker image) is available on the release page. For automation,
The URL will follow the pattern:

- `https://gitlab.com/alleles/ella/-/releases/${TAG}/downloads/ella-release-${TAG}.sif`


### Building the image

#### Docker

Although not recommended, you can build a production ELLA image using make:

``` bash
make _release-build-docker RELEASE_TAG=custom
```

#### Singularity

A singularity image can be built directly from the docker release image:

```shell
singularity pull docker://registry.gitlab.com/alleles/ella:${TAG}
```

## Mount points

There are several directories you will want to mount from the host OS into the container.

| Destination | Description                                             |
| ----------- | ------------------------------------------------------- |
| `/data`     | Data files (details below)                              |
| `/logs`     | API / supervisor log files                              |
| `/tmp`      | Using host `/tmp` can increase performance _(optional)_ |


## Data directory

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

## Setup environment variables

There are a few environment variables that should be set. Check the relavent [Docker](https://docs.docker.com/engine/reference/commandline/run/#set-environment-variables--e---env---env-file)
and/or [Singularity](https://docs.sylabs.io/guides/3.10/user-guide/environment_and_metadata.html#environment-from-the-host)
documentation for how to pass this information to the container.

| Variable            | Description                                              | Example/Default value             |
| :------------------ | :------------------------------------------------------- | :-------------------------------- |
| `PORT`              | Listen port for nginx                                    | Default: `3114`                   |
| `DB_URL`            | URI with PostgreSQL credentials                          | `postgresql://dbuser@host/dbname` |
| `ELLA_CONFIG`       | Application configuration                                | `/data/ella_config.yml`           |
| `ANALYSES_INCOMING` | Path used by the watcher for auto-importing new analyses | `/data/analyses/incoming`         |
| `ANALYSES_PATH`     | Path to analyses that have already been imported         | `/data/analyses/imported`         |
| `IGV_DATA`          | Path to IGV resources                                    | `/data/igv_data`                  |

Additional environment variables can be utilized in the [Application configuration](/technical/application.md).


<!--

This is useful information, but this is not a good place for it.

---

The default entrypoint is `ops/prod/entrypoint.sh`, which will in turn start Supervisor to manage the different processes.

### Behind the scenes

Internally, the `supervisord` will spin up several services:

  - nginx - acting as reverse proxy and serving static files
  - gunicorn - launching several API workers
  - analyses-watcher - handles watching for and importing new analyses
  - polling - watches for and handles new import jobs
 -->

TODO:

- fetch / setup fixtures
  - `ella-cli igv-download`
  - genepanels
  - usergroups
  - filterconfigs
  - users
- create initial database
- load fixture data
- start supervisor processes

## Creating the production database

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


## Populate reference table

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

## Configure ELLA

See [Application configuration](/technical/application.md) for settings related to setup of the ELLA application, as well as [Configuration](/technical/configuration.md) for other options.