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
    sass = require('gulp-sass'),
    plumber = require('gulp-plumber'),
    watch = require('gulp-watch'),
    source = require('vinyl-source-stream'),
    buffer = require('vinyl-buffer'),
    browserify = require('browserify'),
    notify = require('gulp-notify'),
    templateCache = require('gulp-angular-templatecache'),
    os = require('os'),
    path = require('path'),
    __basedir = 'src/webui/dev/';

var production = !!util.env.production;

if(! production) {
    var watchify   = require('watchify'),
        KarmaServer = require('karma').Server;
}

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

var onError = function(err) {
    console.error('\033[31m ERROR:' + err.message + '\033[91m');
};
/*
 * Compile thirdparty javascript
 */
gulp.task('tp-js', function() {
    var sourcePaths = [
        './node_modules/js-polyfills/polyfill.min.js',
        'src/webui/src/thirdparty/angular/1.5.0-rc2/angular.js',
        'src/webui/src/thirdparty/angular/1.5.0-rc2/angular-resource.js',
        'src/webui/src/thirdparty/angular/1.5.0-rc2/angular-animate.js',
        'src/webui/src/thirdparty/angular/1.5.0-rc2/angular-route.js',
        'src/webui/src/thirdparty/angular/1.5.0-rc2/angular-cookies.js',
        'src/webui/src/thirdparty/angularui-bootstrap/ui-bootstrap-tpls-1.1.1.min.js',
        'src/webui/src/thirdparty/ui-router/angular-ui-router.min.js',
        'src/webui/src/thirdparty/angular-clipboard/angular-clipboard.js',
        'src/webui/src/thirdparty/angular-toastr/angular-toastr.tpls.min.js',
        'src/webui/src/thirdparty/autosize-textarea/autosize.min.js',
        'src/webui/src/thirdparty/color-hash/color-hash.js',
        'src/webui/src/thirdparty/checklist-model/checklist-model.js',
        'src/webui/src/thirdparty/dalliance/release-0.13/dalliance-compiled.js',
        'src/webui/src/thirdparty/thenby/thenBy.min.js',
        'src/webui/src/thirdparty/igv/jquery.min.js',  // <-- Beware, we're using jquery here (in case of conflicts)
        'src/webui/src/thirdparty/igv/jquery-ui.min.js',
        'src/webui/src/thirdparty/igv/igv-1.0.5.min.js',
        'src/webui/src/thirdparty/wysiwygjs/wysiwyg.js',
        'src/webui/src/thirdparty/vanilla-color-picker/vanilla-color-picker.min.js'

    ];

    return gulp.src(sourcePaths)
        .pipe(plumber())
        .pipe(concat('thirdparty.js'))
        .pipe(production ? uglify() : util.noop())
        .pipe(gulp.dest(__basedir));
});

var bundler = browserify('./src/webui/src/js/index.js', {
    debug: production ? false : true,
    cache: {}, packageCache: {}, fullPaths: true // for watchify
}).transform(babelify.configure({
    presets: ["es2015", "stage-0"],
    plugins: ["babel-plugin-transform-decorators-legacy"]
}));

function doBundling(watcher) {
    d = new Date(); console.log(
      '[' + d.toTimeString().split(' ')[0] + ']' + ' Started bundling...'
    );

    watcher
        .bundle()
        .on('error', function(err) { onError(err); this.emit('end'); })
        .pipe(plumber({
            errorHandler: onError
        }))
        .pipe(source('app.js'))
        .pipe(buffer())
        .pipe(gulp.dest(__basedir))
        .on('end', function() { d = new Date(); console.log(
                '[' + d.toTimeString().split(' ')[0] + ']' + ' Finished rebuilding JS.'
        )})
        .pipe(production ? util.noop() : livereload());

}

gulp.task('watch-js', function() {
    var watcher  = watchify(bundler, {
        // docker-machine: use 'true' since inotify doesn't seem to work;
        // Docker for Mac: use 'false' since polling makes CPU go crazy
        poll: false
    });
    watcher
        .on('update', function () { doBundling(watcher); });

    doBundling(watcher); // Run the bundle the first time (required for Watchify to kick in)

    return watcher;
});

/*
 * Compile app javascript
 * Transpiles ES6 to ES5
 */
gulp.task('js', function(done) {
    console.log('Gulp: starting js');
    // return browserify('./src/webui/src/js/index.js', {debug: true})
    return bundler
        .bundle()
        .on('error', function(err) { onError(err); this.emit('end'); })
        .pipe(plumber({
            errorHandler: onError
        }))
        .pipe(source('app.js'))
        .pipe(buffer())
        .pipe(gulp.dest(__basedir))
        .pipe(production ? util.noop() : livereload())
        .pipe(production ? uglify() : util.noop());
});

gulp.task('ngtmpl', function() {
    console.log('Gulp: starting ngtmpl');
    return gulp.src('**/*.ngtmpl.html')
        .pipe(templateCache('templates.js', {
            transformUrl: function(file) {return 'ngtmpl/' + path.basename(file)},
            standalone: true
        }))
        .pipe(gulp.dest(__basedir))
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

gulp.task('base-css', function () {
  gulp.src('src/webui/src/css/base.css')
    .pipe(gulp.dest(__basedir));
});


/*
 * Copy required fonts
 */
gulp.task('fonts', function () {
    gulp.src(
        [ 'src/webui/src/thirdparty/fonts/*.woff2' ])
        .pipe(plumber())
        .pipe(gulp.dest(__basedir + 'fonts/'));
});

/**
 * Run unit test once and exit
 * #TODO: hangs (forever) if error in bundling (i.e. syntax file in code)
 */
gulp.task('unit', ['tp-js', 'js', 'ngtmpl'], function (done) {
    var server = new KarmaServer({
      configFile: __dirname + '/src/webui/tests/karma.conf.js',
      singleRun: true,
        autoWatch: false
    }, karmaCompleted);

    server.start();

    function karmaCompleted(karmaResult) {
        if (karmaResult === 1) {
            done('Karma: tests failed with code ' + karmaResult);
        } else {
            done();
        }
    }

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
    watch('src/webui/src/sass/*.scss', function(hmm) {
        console.log('*.scss changed');
        gulp.start('sass')
        });
    watch('src/webui/src/**/*.html', function() {
        console.log('*.html changed');
        gulp.start(['ngtmpl', 'index']);
    });
});


gulp.task('build', ['index', 'tp-js', 'js', 'ngtmpl', 'fonts', 'sass', 'base-css']);

gulp.task('default', ['build','watch-js', 'watch']);
// gulp.task('default', ['build']);
