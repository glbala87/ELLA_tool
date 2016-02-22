var gulp = require('gulp'),
    uglify = require('gulp-uglify'),
    util = require('gulp-util'),
    cssnano = require('gulp-cssnano'),
    autoprefixer = require('gulp-autoprefixer'),
    flatten = require('gulp-flatten'),
    concat = require('gulp-concat'),
    babelify = require("babelify"),
    livereload = require('gulp-livereload'),
    wrapper = require('gulp-wrapper'),
    less = require('gulp-less'),
    sass = require('gulp-sass'),
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
    console.error('\033[31m ERROR:' + err.message + '\033[91m');
};
/*
 * Compile thirdparty javascript
 */
gulp.task('tp-js', function() {
    var sourcePaths = [
        './node_modules/js-polyfills/polyfill.min.js',
        //'./node_modules/js-polyfills/es6.js',
        //'./node_modules/gulp-babel/node_modules/babel-core/browser-polyfill.js',
        'src/webui/src/thirdparty/angular/1.5.0-rc2/angular.js',
        'src/webui/src/thirdparty/angular/1.5.0-rc2/angular-resource.js',
        'src/webui/src/thirdparty/angular/1.5.0-rc2/angular-animate.js',
        'src/webui/src/thirdparty/angular/1.5.0-rc2/angular-route.js',
        'src/webui/src/thirdparty/angular/1.5.0-rc2/angular-cookies.js',
        'src/webui/src/thirdparty/angularui-bootstrap/ui-bootstrap-tpls-1.1.1.min.js',
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
        .on('error', function(err) { onError(err); this.emit('end'); })
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

// SASS
gulp.task('sass', function () {
    gulp.src('src/webui/src/sass/*.scss')
        .pipe(plumber())
        .pipe(sass().on('error', sass.logError))
        .pipe(concat('app.css'))
        .pipe(autoprefixer({
          browsers: ['last 2 versions'],
          cascade: false
          }))
        .pipe(production ? cssnano() : util.noop())
        .pipe(gulp.dest(__basedir))
        .pipe(production ? util.noop() : livereload());
});

gulp.task('less', function () {
    gulp.src('src/webui/src/less/styles.less')
        .pipe(plumber())
        .pipe(less())
        .pipe(concat('base.css'))
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
            'src/webui/src/thirdparty/fontawesome/font-awesome-4.3.0/fonts/*',
            'src/webui/src/thirdparty/fonts/*.woff2'
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
    gulp.watch('src/webui/src/sass/*.scss', ['sass']);
    gulp.watch('src/webui/src/less/**/*.less', ['less']);
    gulp.watch('src/webui/src/**/*.html', ['ngtmpl', 'index']);
});


gulp.task('build', ['index', 'tp-js', 'js', 'ngtmpl', 'fonts', 'sass', 'less']);

gulp.task('default', ['build', 'watch']);
