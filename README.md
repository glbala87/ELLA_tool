The GenAP interpreter is a web app based on AngularJS with a Flask REST backend.

# Development

To start development env with Docker, run **`bin/dev`**

The Dockerfile will read the current `gulpfile.js` and `requirements.txt` and spawn an environment that satisfies these requirements. All Python requirements are installed globally, no virtualenv needed since we're already in an isolated container. Node things are installed to `/dist/node_modules`, gulp is installed both there and globally.

A postgresql instance will also spawn and be automatically linked to the application. To populate the database you can visit the `/reset` route or click on one of the reset buttons in the UI.

# Testing

Test suites are designed to be run under Docker. There are two runner-scripts available:

- **`bin/test-ci`**: should be run *without* any other genap environments running in Docker. It will spawn a new environment, run all tests, and exit.
- **`bin/test-local`**: should be run when genap has already been started (through `bin/dev`). It will simply run tests inside the existing environment - *by default it only runs the non-API tests*.

# Production

### gunicorn + nginx

To start a pseudo-production instance you can use **`bin/production`**.

- Compose automatically calls `bin/helpers/start-wsgi`
- Logs will be placed in the genap directory, these should be changed to suit the production environment
- The `/reset` route will automatically be called after server boot
- To reboot/reload changes, simply run `bin/production` again

### CloudFoundry / Medicloud

Several hacks are needed to get Genap running on CloudFoundry.

- Rename `package.json` to anything else, because CloudFoundry doesn't respect typical ignore patterns - and it immediately thinks it found a nodeJS app, hooray!
- Remove the `gulp:` line from `Procfile` - CF doesn't have a (reasonable) way of doing node+python, so we just ignore the node part and pre-build all assets - oh yeah, you should pre-build all your assets now
- `cp ./ops/prod-GIN/manifest.yml .` from the project root
- Then you *should* be OK to do `cf push`, ignore all the warnings pip throws out since CF is behind by a whole major version of pip


# Running outside of Docker

### Manual install

 - Install [node.js](https://nodejs.org/download/)
 - NPM, the Node Package Manager is installed as part as Node.
 - On OSX you can alleviate the need to run as sudo by [following these instructions](https://github.com/sindresorhus/guides/blob/master/npm-global-without-sudo.md). Highly recommended step on OSX.
 - Next run `npm install`. This will install all the build dependencies for you.
 - To run gulp from the command line you might have to run `npm install -g gulp`, which will install gulp globally.

You'll need to run two processes when developing: the build system and the API.

### Build system

To run the build system, simply run the command: `gulp` - this will build the application, add watchers for any file changes, and automatically reload the browser page when you make a change (requires the `livereload` plugin for Firefox/Chrome).

To just build the application, run: `gulp build` - this builds all the files and puts them into the `src/webui/dev/` directory.

### API

The API also is needed to serve the data.

This is done by launching, in another terminal `PYTHONPATH=/genap/src python /genap/src/api/main.py` - if `DEVELOP=true` is set as an environment variable, the API will launch with debug on.

PostgreSQL needs to be running. To use a different user/db than the default, you may set the `DB_URL` environment variable.
