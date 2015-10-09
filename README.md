
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


## Production

Currently the production files are checked into `src/webui/prod`. They are served by the API when running without the `--dev` option.
