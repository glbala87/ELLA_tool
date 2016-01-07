// Karma configuration
// Generated on Mon Dec 28 2015 15:39:35 GMT+0000 (UTC)

module.exports = function(config) {
  config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: '',


    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: ['jasmine'],


    // list of files / patterns to load in the browser (relative to karma.conf.js)
      files: [
          "../../../node_modules/js-polyfills/es6.js",
          "../src/thirdparty/angular/1.4.0/angular.js",
          "../src/thirdparty/angular/1.4.0/angular-mocks.js",
          "../src/thirdparty/angular/1.4.0/angular-animate.js",
          "../src/thirdparty/angular/1.4.0/angular-aria.js",
          "../src/thirdparty/angular/1.4.0/angular-cookies.js",
          "../src/thirdparty/angular/1.4.0/angular-loader.js",
          "../src/thirdparty/angular/1.4.0/angular-message-format.js",
          "../src/thirdparty/angular/1.4.0/angular-messages.js",
          "../src/thirdparty/angular/1.4.0/angular-resource.js",
          "../src/thirdparty/angular/1.4.0/angular-route.js",
          "../src/thirdparty/angular/1.4.0/angular-sanitize.js",
          //"../src/thirdparty/angular/1.4.0/angular-scenario.js", // causes an error loading tests
          "../src/thirdparty/angular/1.4.0/angular-touch.js",
        "../src/thirdparty/angularui-bootstrap/ui-bootstrap-tpls-0.13.4.min.js",
        "../src/thirdparty/checklist-model/*.js",
        "../src/thirdparty/color-hash/*.js",
        "../src/thirdparty/dalliance/release-0.13/*.js",
        "../src/thirdparty/thenBy/*.js",
        "../src/thirdparty/ui-router/*.js",
        //"../src/js/**/*.js",
        "../dev/app.js",
        "./unit/*.js"
    ],


    // list of files to exclude
    exclude: [
        "../src/thirdparty/angular/1.4.0/*.min.js"
    ],


    // preprocess matching files before serving them to the browser
    // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
    // The coverage preprocessor gets in the way of debugging!
    preprocessors: {
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
    logLevel: config.LOG_INFO,
    //logLevel: config.LOG_DEBUG,


    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: false,


    // start these browsers
    // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
      browsers: ['PhantomJS'],
      //browsers: ['Chrome'],


    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: false,

    // Concurrency level
    // how many browser should be started simultaneous
    concurrency: Infinity
  })
}
