ella is a web app based on AngularJS with a Flask REST backend.

Most functionality is now baked into a Makefile, run `make help` to see a quick overview of available commands.

# Development

### Getting started:
- Start a development environment in Docker, run **`make dev`** - you may need to do `make build` first
- Populate the database by visiting the `/reset` route _or do `/reset?testset=all` to get an expanded data set_.

### More info:
- All *system* dependencies - as in apt-packages
  - are kept in core images (e.g. `ousamg/ella-core:0.9.1`)
  - are managed via the build system `ops/builder/builder.yml`
- All *application* dependencies - nodejs, python, etc.
  - are kept in local images (e.g. `local/ella-dev`)
  - are managed via their respective dependency files
  - are baked in when you do `make build`, so if you change a dependency file you need to do `make build` again!

# Testing

Our test suites are intended to be run inside Docker. The Makefile has commands to do run setup and the tests themselves.

## Getting started
- `make test` will run all (js, api, and common) tests _excluding e2e tests_
- `make e2e-test` will run e2e tests
- `make single-test` will run a single _non-e2e_ test

To clean up docker containers when e2e tests fail: `make cleanup-e2e BRANCH=test`

## More info
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

# Protractor - e2e testing tool
Protractor is an Angular friendly wrapper around WebDriver. 
See http://www.protractortest.org
  
## Setup
- Create a separate folder outside the Ella source repo.
- Copy ops/dev/package-protractor.json to package.json
- Install node modules: `npm install`
- Install selenium. `npm run-script init`

A npm script 'protractor' in package.json ensures that the locally installed binaries in node_modules are used.
Running bare `protractor` will use your globally installed protractor (if you have one) and could cause 'library not found'-errors.

## Explore
Start a Repl:	
`npm run-script protractor --  --elementExplorer --directConnect --baseUrl <url to your running app>`

Try out protractor/WebDriver selectors and commands before putting them in your spec files.
This works for an Angular app only.


## Run e2e test
If the tests fail in CI, it can be useful to run them locally:
`npm run-script protractor -- <path to protractor conf file> --specs <path to you spec file> --baseUrl <url of your running app>`
This automatically launches a Selenium server (the one installed through the `run-script-init` or `webdriver-manager update` command).

See https://github.com/angular/protractor/blob/master/docs/debugging.md
