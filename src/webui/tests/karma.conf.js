// Karma configuration
// Generated on Mon Dec 28 2015 15:39:35 GMT+0000 (UTC)

module.exports = function(config) {
  config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: '',

    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: ['jasmine', 'browserify'],


    // list of files / patterns to load in the browser (relative to karma.conf.js)
      files: [
          // TODO: use same polyfill in test and production code
          //"../../../node_modules/babel-es6-polyfill/browser-polyfill.js",
          "../../../node_modules/js-polyfills/es6.js", // needed by phantomjs
          //"../../../node_modules/babel-core/browser-polyfill.js", // gives error in unit tests (phantomjs): TypeError: 'undefined' is not a function (evaluating 'Object.assign(new_options, defaults)')
          "../dev/thirdparty.js",
          //"../src/thirdparty/angular/1.4.0/angular-mocks.js",
        //"../src/js/**/*.js",
        "../dev/app.js", // TODO: consider including individual src files once transpiling is configured in karma
        "./unit/filters.spec.js",
        "./unit/analysislist.spec.js",
        //"../src/js/views/**/*.ngtmpl.html",
        "../dev/**/*.ngtmpl.html",
        // e7:
          "../src/js/oentries.js",
          "./unit/oentries.spec.js",
        // vanilla e6:
          "../src/js/ng-decorators.js",
          "../src/js/e6stuff.js",
          "./unit/e6stuff.spec.js",
        // e6 with custom decorators:
          "./unit/e6.decorator.spec.js",
          "./unit/e6.service.spec.js",
          "../src/js/services/e6.service.js"
    ],

    // list of files to exclude
    exclude: [
        "../src/thirdparty/angular/1.4.0/*.min.js"
    ],

      ngHtml2JsPreprocessor: {
          // strip this from the file path
          stripPrefix: '/genap/src/webui/dev/',
          // stripSuffix: '.ext',
          // prepend this to the
          //prependPrefix: 'served/',

          moduleName: 'templates'
      },

    // preprocess matching files before serving them to the browser
    // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
    // The coverage preprocessor gets in the way of debugging!

    // Note! no comma after last object member:
    preprocessors: { // only tests and templates?
        '../dev/ngtmpl/*.ngtmpl.html': ['ng-html2js'],
        // '../src/js/**/*.js': ['browserify'],
        //'./unit/**/*.spec.js': ['browserify']
        '../src/js/ng-decorators.js': ['browserify'],
        './unit/filters.spec.js' : ['browserify'],
        '../src/js/e6stuff.js': ['browserify'],
        './unit/e6stuff.spec.js' : ['browserify'],
        '../src/js/oentries.js': ['browserify'],
        './unit/oentries.spec.js' : ['browserify'],
        './unit/e6.decorator.spec.js': ['browserify'],
        '../src/js/services/e6.service.js': ['browserify'],
        './unit/e6.service.spec.js' : ['browserify']

    },

      browserify: {
          debug: true,
          transform:  [["babelify", { "presets": ["es2015", "stage-0"],
                                      "plugins": ["babel-plugin-transform-decorators-legacy"]
                                    }]]
      },

    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
    //reporters: ['progress'],
    reporters: ['mocha'],

    // config of mochaReporter https://www.npmjs.com/package/karma-mocha-reporter
    mochaReporter: {
          output: 'autowatch'
    },

    // web server port
    port: 9876,


    // enable / disable colors in the output (reporters and logs)
    colors: true,


    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    //logLevel: config.LOG_INFO,
    logLevel: config.LOG_DEBUG,


    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: false,

      // Continuous Integration mode
      // if true, Karma captures browsers, runs the tests and exits
      singleRun: false,

    // start these browsers
    // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
      browsers: ['PhantomJS'],
      //browsers: ['Chrome'],



    // Concurrency level
    // how many browser should be started simultaneous
    concurrency: Infinity
  })
}
