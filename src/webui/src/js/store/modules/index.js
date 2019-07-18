import { Module } from 'cerebral'
import HttpProvider from '@cerebral/http'
import StorageModule from '@cerebral/storage'

import AppModule from './app'
import SearchModule from './search'
import ViewsModule from './views'
import Router from '@cerebral/router'
import AppRouter from './router'
import { IntervalProvider, ProgressProvider, ClipboardProvider } from '../common/providers/'
import onBeforeUnload from '../common/providers/onBeforeUnload'
import toastProvider from '../common/providers/toastProvider'

let http = HttpProvider({
    baseUrl: '/api/v1/',
    headers: {
        'Content-Type': 'application/json; charset=UTF-8',
        Accept: 'application/json'
    },
    onRequest(xhr, options) {
        if (options.headers['Content-Type'].indexOf('application/x-www-form-urlencoded') >= 0) {
            options.body = urlEncode(options.body)
        } else if (options.headers['Content-Type'].indexOf('application/json') >= 0) {
            // Only this line is changed from default
            options.body = angular.toJson(options.body)
        }

        if (
            typeof window !== 'undefined' &&
            window.FormData &&
            options.body instanceof window.FormData
        ) {
            delete options.headers['Content-Type']
        }

        xhr.withCredentials = Boolean(options.withCredentials)

        Object.keys(options.headers).forEach((key) => {
            xhr.setRequestHeader(key, options.headers[key])
        })

        if (options.onRequestCallback) {
            options.onRequestCallback(xhr)
        }

        xhr.send(options.body)
    }
})

const storage = StorageModule({
    target: localStorage,
    json: true,
    sync: {},
    prefix: 'app'
})

/**
 *
 * @param Boolean withRouter Exclude router when using Module for testing
 */
function RootModule(withRouter = true) {
    return Module({
        state: {},
        modules: {
            storage,
            search: SearchModule,
            views: ViewsModule,
            app: AppModule,
            router: withRouter
                ? AppRouter
                : Router({
                      routes: [
                          {
                              path: '/*',
                              signal: ''
                          }
                      ]
                  }) // Empty router -> Karma messes up when unit testing
        },
        signals: {},
        providers: {
            progress: ProgressProvider,
            onBeforeUnload,
            interval: IntervalProvider,
            clipboard: ClipboardProvider,
            toast: toastProvider,
            http
        },
        services: ['CustomAnnotationModal', 'ReferenceEvalModal', 'ImportModal', 'Config', 'User']
    })
}

export default RootModule
