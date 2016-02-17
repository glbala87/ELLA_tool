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
    sass = require('gulp-sass'),
    plumber = require('gulp-plumber'),
    source = require('vinyl-source-stream'),
    buffer = require('vinyl-buffer'),
    browserify = require('browserify'),
    notify = require('gulp-notify'),
    protractor = require('gulp-protractor').protractor,
    KarmaServer = require('karma').Server,
    os = require('os'),
    __basedir = 'src/webui/dev/';

function getIpAddress() {
    var ipAddress = null;
    var ifaces = os.networkInterfaces();

    function processDetails(details) {
        if (details.family === 'IPv4' && details.address !== '127.0.0.1' && !ipAddress) {
            ipAddress = details.address;
        }
    }

    for (var dev in ifaces) {
        ifaces[dev].forEach(processDetails);
    }
    return ipAddress;
}

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

// SASS
gulp.task('sass', function () {
    gulp.src('src/webui/src/sass/*.scss')
        .pipe(plumber())
        .pipe(sass().on('error', sass.logError))
        .pipe(concat('app.css'))
        .pipe(production ? minifyCss({compatibility: 'ie8'}) : util.noop())
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
    var base = util.env.e2e_ip || '172.16.250.128';
    var basePort = util.env.e2e_port || 8000
    var seleniumAddress = util.env.selenium_address || 'http://172.16.250.128:4444/wd/hub';
    var args = ['--baseUrl', 'http://' + base + ':' + basePort,
                '--seleniumAddress', seleniumAddress
    ];


    var http = require('http');
    var options = {
        host: base,
        port: basePort,
        path: '/analyses'
    };

    callback = function(response) {
        var str = '';

        //another chunk of data has been recieved, so append it to `str`
        response.on('data', function (chunk) {
            str += chunk;
        });

        //the whole response has been recieved, so we just print it out here
        response.on('end', function () {
            console.log(str);
        });
    }

    console.log('Checking connection to ' + base + ':' + basePort);
    http.request(options, callback).end();

    gulp.src(["./src/webui/tests/e2e/spec.js"])
        .pipe(protractor({
            configFile: "./src/webui/tests/protractor.conf.js",
            args: args
        }))
        .on('error', function(e) { console.error(e.message); throw e;});
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
