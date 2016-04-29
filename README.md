ella is a web app based on AngularJS with a Flask REST backend.

Most functionality is now baked into a Makefile, run `make help` to see a quick overview of available commands.

# Development

### Getting started:
- Start a development environment in Docker, run **`make dev`** - you may need to do `make build` first
- Populate the database by visiting the `/reset` route _or do `/reset?all=true` to get an expanded data set_.

### More info:
- All *system* dependencies - as in apt-packages
  - are kept in core images (e.g. `ousamg/ella-core:0.9.1`)
  - are managed via the build system `ops/builder/builder.yml`
- All *application* dependencies - nodejs, python, etc.
  - are kept in local images (e.g. `local/ella-dev`)
  - are managed via their respective dependency files
  - are baked in when you do `make build`, so if you change a dependency file you need to do `make build` again!

# Testing

### Getting started:
- `make test` will run all (js, api, and common) tests _excluding e2e tests_
- `make e2e-test` will run e2e tests
- `make single-test` will run a single _non-e2e_ test

To clean up docker containers when e2e tests fail: `make cleanup-e2e BRANCH=test`

### More info:
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
