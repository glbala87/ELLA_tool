const path = require('path')
const MiniCssExtractPlugin = require('mini-css-extract-plugin')
const HtmlWebpackPlugin = require('html-webpack-plugin')
const CleanWebpackPlugin = require('clean-webpack-plugin')
const LivereloadWebpackPlugin = require('webpack-livereload-plugin')
const DeadcodeWebpackPlugin = require('webpack-deadcode-plugin')
const md5File = require('md5-file')

LivereloadWebpackPlugin.prototype.done = function done(stats) {
    this.fileHashes = this.fileHashes || {}

    const fileHashes = {}
    for (let file of Object.keys(stats.compilation.assets)) {
        fileHashes[file] = md5File.sync(stats.compilation.assets[file].existsAt)
    }

    const toInclude = Object.keys(fileHashes).filter((file) => {
        if (this.ignore && file.match(this.ignore)) {
            return false
        }
        return !(file in this.fileHashes) || this.fileHashes[file] !== fileHashes[file]
    })

    if (this.isRunning && toInclude.length) {
        this.fileHashes = fileHashes
        console.log('Live Reload: Reloading ' + toInclude.join(', '))
        setTimeout(
            function onTimeout() {
                this.server.notifyClients(toInclude)
            }.bind(this)
        )
    }
}

module.exports = (env, argv) => {
    const production = argv.mode === 'production'

    return {
        entry: {
            app: './src/webui/src/js/index.js'
        },
        performance: { hints: false }, // Disable asset size warning
        output: {
            path: path.resolve(__dirname, 'src/webui/build/'),
            filename: '[name].js'
        },
        devtool: production ? 'source-map' : 'inline-source-map', // inline-source-map is very large, but better
        module: {
            rules: [
                {
                    test: /\.js?$/,
                    loader: 'babel-loader',
                    exclude: /node_modules/,
                    query: {
                        cacheDirectory: true
                    }
                },
                {
                    test: /\.(sa|sc|c)ss$/,
                    use: [MiniCssExtractPlugin.loader, 'css-loader', 'sass-loader']
                },
                // Loads all files with ngtmpl.html into 'templates' module in angular
                {
                    test: /\.ngtmpl\.html$/,
                    loader: 'ng-cache-loader?prefix=&module=templates'
                },
                {
                    test: /\.(woff(2)?|ttf|eot|svg)$/,
                    use: [
                        {
                            loader: 'file-loader',
                            options: {
                                name: '[name].[ext]',
                                outputPath: 'fonts/'
                            }
                        }
                    ]
                }
            ]
        },
        plugins: [
            // Creates separate css file
            new MiniCssExtractPlugin({
                filename: '[name].css'
            }),
            // Creates index.html with automatic <script> tags
            new HtmlWebpackPlugin({ template: './src/webui/src/index.html' }),
            new CleanWebpackPlugin([path.resolve(__dirname, 'src/webui/build/*')], {
                verbose: true
            }),
            new LivereloadWebpackPlugin(),
            new DeadcodeWebpackPlugin({
                patterns: ['src/webui/src/**/*.(js|css|html)'],
                exclude: ['**/*.spec.js']
            })
        ]
    }
}
