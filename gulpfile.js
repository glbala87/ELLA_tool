var gulp = require('gulp'),
    uglify = require('gulp-uglify'),
    util = require('gulp-util'),
    minifyCss = require('gulp-minify-css'),
    flatten = require('gulp-flatten'),
    concat = require('gulp-concat'),
    babelify = require("babelify"),
    livereload = require('gulp-livereload'),
    wrapper = require('gulp-wrapper'),
    less = require('gulp-less'),
    plumber = require('gulp-plumber'),
    source = require('vinyl-source-stream'),
    buffer = require('vinyl-buffer'),
    browserify = require('browserify'),
    notify = require('gulp-notify'),
    protractor = require('gulp-protractor').protractor,
    KarmaServer = require('karma').Server,
    __basedir = 'src/webui/dev/';

var production = !!util.env.production;

var onError = function(err) {
    console.error(err.message);
    notify.onError()(err);
    this.emit('end');
};
/*
 * Compile thirdparty javascript
 */
gulp.task('tp-js', function() {
    var sourcePaths = [
        //'./node_modules/babel-es6-polyfill/browser-polyfill.js',
        //'./node_modules/js-polyfills/es6.js',
        'src/webui/src/thirdparty/angular/1.4.0/angular.js',
        'src/webui/src/thirdparty/angular/1.4.0/angular-resource.js',
        'src/webui/src/thirdparty/angular/1.4.0/angular-animate.js',
        'src/webui/src/thirdparty/angular/1.4.0/angular-route.js',
        'src/webui/src/thirdparty/angular/1.4.0/angular-cookies.js',
        'src/webui/src/thirdparty/angularui-bootstrap/ui-bootstrap-tpls-0.13.4.min.js',
        'src/webui/src/thirdparty/ui-router/angular-ui-router.min.js',
        'src/webui/src/thirdparty/color-hash/color-hash.js',
        'src/webui/src/thirdparty/checklist-model/checklist-model.js',
        'src/webui/src/thirdparty/dalliance/release-0.13/dalliance-compiled.js',
        'src/webui/src/thirdparty/thenby/thenBy.min.js'
    ];

    return gulp.src(sourcePaths)
        .pipe(plumber())
        .pipe(concat('thirdparty.js'))
        .pipe(uglify())
        .pipe(gulp.dest(__basedir));
});

/*
 * Compile app javascript
 * Transpiles ES6 to ES5
 */
gulp.task('js', function() {
    return browserify('./src/webui/src/js/index.js', {debug: true})
        .transform(babelify.configure({
            //optional: ["es7.decorators"]
            presets: ["es2015", "stage-0"],
            plugins: ["babel-plugin-transform-decorators-legacy"]
        }))
        .bundle()
        .on('error', function(err) { console.error(err.message); this.emit('end'); })
        .pipe(plumber({
            errorHandler: onError
        }))
        .pipe(source('app.js'))
        .pipe(buffer())
        .pipe(gulp.dest(__basedir))
        .pipe(production ? util.noop() : livereload());
});

gulp.task('ngtmpl', function() {
    return gulp.src('**/*.ngtmpl.html')
        .pipe(plumber())
        .pipe(flatten())
        .pipe(gulp.dest(__basedir + 'ngtmpl/'))
        .pipe(production ? util.noop() : livereload());
});

gulp.task('index', function() {
    return gulp.src('src/webui/src/index.html')
        .pipe(plumber())
        .pipe(gulp.dest(__basedir));
});

/*
 * Compile css from less files
 */
gulp.task('less', function () {
    gulp.src('src/webui/src/less/styles.less')
        .pipe(plumber())
        .pipe(less())
        .pipe(concat('app.css'))
        .pipe(production ? minifyCss({compatibility: 'ie8'}) : util.noop())
        .pipe(gulp.dest(__basedir))
        .pipe(production ? util.noop() : livereload());
});

/*
 * Copy required fonts
 */
gulp.task('fonts', function () {
    gulp.src(
        [
            'src/webui/src/thirdparty/fontawesome/font-awesome-4.3.0/fonts/*.{woff,woff2,eot,svg,ttf,otf}'
        ])
        .pipe(plumber())
        .pipe(gulp.dest(__basedir + 'fonts/'));
});

''
/**
 * Run end-2-end tests
 */

gulp.task('e2e', function(done) {
    var args = ['--baseUrl', 'http://172.16.250.128:5000', // our app running in docker. The IP will change!
                '--seleniumAddress', 'http://172.16.250.128:4444/wd/hub', // selenium server
    ];
    gulp.src(["./src/webui/tests/e2e/spec.js"])
        .pipe(protractor({
            configFile: "./src/webui/tests/protractor.conf.js",
            args: args
        }))
        .on('error', function(e) { throw e; });
});

/**
 * Run unit test once and exit
 */
gulp.task('unit', ['tp-js', 'js', 'ngtmpl'], function (done) {
    new KarmaServer({
	configFile: __dirname + '/src/webui/tests/karma.conf.js',
	singleRun: true,
    autoWatch: false

    }, function(karmaExitStatus) {
        if (karmaExitStatus) {
            process.exit(1);
        };
    }).start();
});

/**
 * Rerun unit tests as code change
 */

gulp.task('unit-auto', ['tp-js', 'js'], function (done) {
    new KarmaServer({
        configFile: __dirname + '/src/webui/tests/karma.conf.js',
        singleRun: false,
        autoWatch: true // karma watches files in 'files:' in karma.conf.js
    }, done).start();
});

gulp.task('watch', function() {
    livereload.listen();
    gulp.watch('src/webui/src/js/**/*.js', ['js']);
    gulp.watch('src/webui/src/less/**/*.less', ['less']);
    gulp.watch('src/webui/src/**/*.html', ['ngtmpl', 'index']);
});


gulp.task('build', ['index', 'tp-js', 'js', 'ngtmpl', 'fonts', 'less']);

gulp.task('default', ['build', 'watch']);
