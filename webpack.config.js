const path = require('path')
const MiniCssExtractPlugin = require('mini-css-extract-plugin')
const HtmlWebpackPlugin = require('html-webpack-plugin')

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
                        cacheDirectory: true,
                        plugins: ['transform-decorators-legacy'],
                        presets: ['env']
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
            new HtmlWebpackPlugin({ template: './src/webui/src/index.html' })
        ]
    }
}
