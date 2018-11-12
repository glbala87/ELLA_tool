# Deployment

## Production

Only requirement for production deployment is an existing PostgresSQL database.

*ella* uses docker for deployment, making it as easy as running two commands.

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
  - webpack - transpiles the frontend upon startup
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