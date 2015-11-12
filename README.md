
# GenAP interpreter

The GenAP interpreter is a web app based on AngularJS with a Flask REST backend.

## Development

Docker is now the recommended way to do development.

**To start development env with Docker, run `docker-compose up`**

The Dockerfile will read the current `gulpfile.js` and `requirements.txt` and spawn an environment that satisfies these requirements. All Python requirements are installed globally, no virtualenv needed since we're already in an isolated container. Node things are installed to `/dist/node_modules`, gulp is installed both there and globally.

A postgresql instance will also spawn and be automatically linked to the application. To populate the database you can visit the `/reset` route or click on one of the reset buttons in the UI.

## Testing

Test suites are designed to be run under Docker. There are two runner-scripts available:

- `test-ci.sh`: should be run without any other genap environments running in Docker. It will spawn a new environment, run all tests, and exit.
- `test-local.sh`: should be run when genap has already been started (through `docker-compose up`). It will simply run tests inside the existing environment - by default it only runs the non-API tests.

All helper-scripts now live in `exe`, so as additional test scripts are needed/created, they should go into `exe` and be run from the main two runners.

## Production

#### gunicorn + nginx

To start a production instance you can use `docker-compose -f docker-compose-production.yml up`.

This will start a postgresql database instance and link it to the genap container - which you probably don't want - so you can set the location of your postgresql database in the above YAML file (there's a commented line).

- Logs will be placed in the genap directory, these should be changed to suit the production environment
- nginx and gunicorn will communicate using a unix socket
- Compose automatically calls `./exe/production.sh` - see that file for other production setup details

#### CloudFoundry / Medicloud

Several hacks are needed to get Genap running on CloudFoundry.

- Rename `package.json` to anything else, because CloudFoundry doesn't respect typical ignore patterns - and it immediately thinks it found a nodeJS app, hooray!
- Remove the `gulp:` line from `Procfile` - CF doesn't have a (reasonable) way of doing node+python, so we just ignore the node part and pre-build all assets - oh yeah, you should pre-build all your assets now
- Then you *should* be OK to do `cf push`, ignore all the warnings pip throws out since CF is behind by a whole major version of pip


## Running outside of Docker (in development)

#### Manual install

 - Install [node.js](https://nodejs.org/download/)
 - NPM, the Node Package Manager is installed as part as Node.
 - On OSX you can alleviate the need to run as sudo by [following these instructions](https://github.com/sindresorhus/guides/blob/master/npm-global-without-sudo.md). Highly recommended step on OSX.
 - Next run `npm install`. This will install all the build dependencies for you.
 - To run gulp from the command line you might have to run `npm install -g gulp`, which will install gulp globally.

You'll need to run two processes when developing: the build system and the API.

#### Build system

To run the build system, simply run the command: `gulp` - this will build the application, add watchers for any file changes, and automatically reload the browser page when you make a change (requires the `livereload` plugin for Firefox/Chrome).

To just build the application, run: `gulp build` - this builds all the files and puts them into the `src/webui/dev/` directory.

#### API

The API also is needed to serve the data.

This is done by launching, in another terminal `genap/exe/api` - if `DEVELOP=true` is set as an environment variable, the API will launch with debug on.

PostgreSQL needs to be running. To use a different user/db than the default, you may set the `DB_URL` environment variable.
