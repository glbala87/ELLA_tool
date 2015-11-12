var gulp = require('gulp'),
    uglify = require('gulp-uglify'),
    util = require('gulp-util'),
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
    __dirname = 'src/webui/dev/';

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
        './node_modules/gulp-babel/node_modules/babel-core/browser-polyfill.js',
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
        .pipe(gulp.dest(__dirname));
});

/*
 * Compile app javascript
 * Transpiles ES6 to ES5
 */
gulp.task('js', function() {
    return browserify('./src/webui/src/js/index.js', {debug: true})
        .transform(babelify.configure({
            optional: ["es7.decorators"]
        }))
        .bundle()
        .on('error', function(err) { console.error(err.message); this.emit('end'); })
        .pipe(plumber({
            errorHandler: onError
        }))
        .pipe(source('app.js'))
        .pipe(buffer())
        .pipe(gulp.dest(__dirname))
        .pipe(production ? util.noop() : livereload());
});

gulp.task('ngtmpl', function() {
    return gulp.src('**/*.ngtmpl.html')
        .pipe(plumber())
        .pipe(flatten())
        .pipe(gulp.dest(__dirname + 'ngtmpl/'))
        .pipe(production ? util.noop() : livereload());
});

gulp.task('index', function() {
    return gulp.src('src/webui/src/index.html')
        .pipe(plumber())
        .pipe(gulp.dest(__dirname));
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
        .pipe(gulp.dest(__dirname))
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
        .pipe(gulp.dest(__dirname + 'fonts/'));
});


gulp.task('watch', function() {
    livereload.listen();
    gulp.watch('src/webui/src/js/**/*.js', ['js']);
    gulp.watch('src/webui/src/less/**/*.less', ['less']);
    gulp.watch('src/webui/src/**/*.html', ['ngtmpl', 'index']);
});


gulp.task('build', ['index', 'tp-js', 'js', 'ngtmpl', 'fonts', 'less']);

gulp.task('default', ['build', 'watch']);
