import Router from '@cerebral/router'

export default Router({
    routes: [
        {
            path: '/overview/:section',
            signal: 'views.overview.routedWithSection'
        },
        {
            path: '/overview/',
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
