
# GenAP interpreter

[![Build Status](http://188.166.24.68:4567/buildStatus/icon?job=genap)](http://188.166.24.68:4567/job/genap/)

The GenAP interpreter is a web app based on AngularJS with a Flask REST backend.

## Development

### Requirements

 - Install [node.js](https://nodejs.org/download/)
 - NPM, the Node Package Manager is installed as part as Node.
 - On OSX you can alleviate the need to run as sudo by [following these instructions](https://github.com/sindresorhus/guides/blob/master/npm-global-without-sudo.md). Highly recommended step on OSX.
 - In order to develop you __need__ to install `gulp` (the build system).  Open a terminal and type:
 ```
 npm install gulp
 ```
 - The other required dependencies for the application can be found at the top of the `gulpfile.js` build file, but they can all be installed at once by typing:
 `npm install -g gulpfile-install` and then `gulpfile-install -f gulpfile.js`

### Running

You'll need to run two processes when developing: the build system and the API.

#### Build system

To run the build system, simply run the command:
```
gulp
```

This will build the application, add watchers for any file changes, and automatically reload the browser page when you make a change (requires the `livereload` plugin for Firefox/Chrome).

To just build the application, run:
```
gulp build
```

This builds all the files and puts them into the `src/webui/dev/` directory.

#### API

The API also needs to serve the data.
This is done by launching, in another terminal:
 - on Linux, using the script `genap/exe/api --dev`
 - on Windows, by navigating to `python genap/src/api/` and running `python main.py --dev`

PostgreSQL needs to be running. To use a different user/db than the default, you may set the DB_URL environment variable.

#### Docker

The Dockerfile will read the current `gulpfile.js` and `requirements.txt` and spawn an environment that satisfies these requirements. All Python requirements are installed globally, no virtualenv needed since we're already in an isolated container. Gulp and nodejs make absolutely no sense, so...
- All nodejs requirements are installed to `/dist/node_modules`, when running inside the container for the first time, run `/genap/exe/dev/docker_gulp_setup.sh` and this will symlink the requirements folder into `/genap` which makes Gulp happy.
- Gulp itself is now installed both globally and locally, so after the above step you can just run `gulp` as described above in the Gulp section.

**Note:** Currently the Docker setup won't spawn a PostgreSQL instance. Nor does it have an easy way to run both gulp and flask at the same time.

## Production

Currently the production files are checked into `src/webui/prod`. They are served by the API when running without the `--dev` option.
