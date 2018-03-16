import { Module } from 'cerebral'
import HttpProvider from '@cerebral/http'
import StorageModule from '@cerebral/storage'
import Router from '@cerebral/router'

import SearchModule from './search'
import ViewsModule from './views'
import AppModule from './app'
import { IntervalProvider, ProgressProvider, ClipboardProvider } from '../common/providers/'
import onBeforeUnload from '../common/providers/onBeforeUnload'
import closeModal from '../common/actions/closeModal'
import showModal from '../common/actions/showModal'

let http = HttpProvider({
    baseUrl: '/api/v1/',
    headers: {
        'Content-Type': 'application/json; charset=UTF-8',
        Accept: 'application/json'
    }
})

const storage = StorageModule({
    target: localStorage,
    json: true,
    sync: {},
    prefix: 'app'
})

export default Module({
    state: {
        modals: {}
    },
    modules: {
        storage,
        search: SearchModule,
        views: ViewsModule,
        app: AppModule,
        router: Router({
            routes: [
                {
                    path: '/overview/:section',
                    signal: 'views.overview.routed'
                },
                {
                    path: '/workflows/analyses/:analysisId',
                    signal: 'views.workflows.routedAnalysis'
                },
                {
                    path: '/workflows/variants/:alleleReference/:alleleIdentifier',
                    signal: 'views.workflows.routedAllele'
                },
                {
                    path: '/dashboard',
                    signal: 'views.dashboard.routed'
                },
                {
                    path: '/login',
                    signal: 'views.login.routed'
                },
                {
                    path: '/*',
                    signal: 'views.defaultRouted'
                }
            ]
        })
    },
    signals: {
        closeModal: [closeModal],
        showModal: [showModal]
    },
    providers: {
        progress: ProgressProvider,
        onBeforeUnload,
        interval: IntervalProvider,
        clipboard: ClipboardProvider,
        http
    },
    services: [
        'toastr',
        'CustomAnnotationModal',
        'ReferenceEvalModal',
        'ImportModal',
        'Config',
        'User',
        '$uibModal'
    ]
})
