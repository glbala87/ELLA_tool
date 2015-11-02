var gulp = require('gulp'),
    concat = require('gulp-concat'),
    uglify = require('gulp-uglify'),
    autoprefixer = require('gulp-autoprefixer');
    flatten = require('gulp-flatten'),
    babel = require("gulp-babel"),
    livereload = require('gulp-livereload'),
    wrapper = require('gulp-wrapper'),
    less = require('gulp-less'),
    plumber = require('gulp-plumber'),
    notify = require('gulp-notify'),
    __dirname = 'src/webui/dev/';


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
    var sourcePaths = [
        'src/webui/src/js/app.js',
        'src/webui/src/js/*.js',
        'src/webui/src/js/**/*.js',
        'src/webui/src/js/**/**/*.js',
        'src/webui/src/js/**/**/**/*.js',
    ];

    return gulp.src(sourcePaths)
        .pipe(plumber({
            errorHandler: onError
        }))
        .pipe(babel())
        .pipe(wrapper({
           header: '\n/* ${filename}: */\n'
        }))
        .pipe(concat('app.js'))
        .pipe(gulp.dest(__dirname))
        .pipe(livereload());
});

gulp.task('ngtmpl', function() {
    return gulp.src('**/*.ngtmpl.html')
        .pipe(plumber())
        .pipe(flatten())
        .pipe(gulp.dest(__dirname + 'ngtmpl/'))
        .pipe(livereload());
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
        .pipe(autoprefixer('last 2 versions'))
        .pipe(gulp.dest(__dirname))
        .pipe(livereload());
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
