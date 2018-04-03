// Karma configuration
// Generated on Mon Dec 28 2015 15:39:35 GMT+0000 (UTC)

module.exports = function(config) {
    config.set({
        // base path that will be used to resolve all patterns (eg. files, exclude)
        basePath: '../build/',

        // frameworks to use
        // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
        frameworks: ['jasmine', 'browserify'],

        // list of files / patterns to load in the browser (relative to karma.conf.js)
        files: [
            '../../../node_modules/js-polyfills/es6.js', // needed by phantomjs
            '../build/thirdparty.js',
            '../src/thirdparty/angular/1.5.0-rc2/angular-mocks.js',
            '../build/app.js',
            '../src/js/**/*.js',
            '../tests/unit/**/*.spec.js',
            '../build/templates.js'
        ],

        // list of files to exclude
        exclude: [
            '../src/thirdparty/angular/1.5.0-rc2/*.min.js',
            '../src/js/widgets/noAllelesWidget.directive.js' // refers to a non-existing workbench variable
        ],

        ngHtml2JsPreprocessor: {
            // Karma's web server loads templates using an absolute url.
            // In some cases the url must be transformed to match the templateUrl given in the angular directive
            //stripPrefix: 'something',
            // stripSuffix: '.ext',
            // prepend this to the
            //prependPrefix: 'served/',

            moduleName: 'templates'
        },

        // preprocess matching files before serving them to the browser
        // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
        // The coverage preprocessor gets in the way of debugging!

        // Note! no comma after last object member:
        preprocessors: {
            '../build/ngtmpl/*.ngtmpl.html': ['ng-html2js'],
            '../tests//unit/**/*.spec.js': ['browserify'],
            '../src/js/**/*.js': ['browserify']
        },

        browserify: {
            debug: true,
            transform: [
                [
                    'babelify',
                    {
                        presets: ['env', 'stage-0'],
                        plugins: ['babel-plugin-transform-decorators-legacy']
                    }
                ]
            ]
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

        // Continuous Integration mode
        // if true, Karma captures browsers, runs the tests and exits
        singleRun: false,

        // start these browsers
        // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
        browsers: ['ChromeHeadless'],

        customLaunchers: {
            ChromeHeadless: {
                base: 'Chrome',
                flags: [
                    // We must disable the Chrome sandbox when running Chrome inside Docker (Chrome's sandbox needs
                    // more permissions than Docker allows by default)
                    '--no-sandbox',
                    // See https://chromium.googlesource.com/chromium/src/+/lkgr/headless/README.md
                    '--headless',
                    '--disable-gpu',
                    // Without a remote debugging port, Google Chrome exits immediately.
                    ' --remote-debugging-port=9222'
                ]
            }
        },

        // Concurrency level
        // how many browser should be started simultaneous
        concurrency: Infinity
    })
}
