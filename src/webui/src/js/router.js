import page from 'page'
import qs from 'query-string'
import { Inject, Run } from './ng-decorators'

// This is all spaghetti due to how the CerebralJS <-> AngularJS integration is setup
// We don't have access to the Cerebral controller object upon initialization, as it's created
// inside the CerebralJS AngularJS binding module.
// The following is confusingly run _after_ the AngularJS config is run, after Cerebral is fully
// configured by AngularJS (see the main index.js and AngularJS documentation on 'run()').

function checkUnsavedInterpretation(state) {
    return (
        'views' in state &&
        'workflows' in state.views &&
        'interpretation' in state.views.workflows &&
        state.views.workflows.interpretation.isOngoing &&
        state.views.workflows.interpretation.dirty
    )
}

class RouterInit {
    @Run()
    @Inject('cerebral')
    init(cerebral) {
        function route(url, signalPath) {
            page(url, (ctx) => {
                const query = qs.parse(ctx.querystring)
                cerebral.controller.getSignal(signalPath)(Object.assign({}, ctx.params, { query }))
            })
        }
        route('/overview/:section', 'views.overview.routedWithSection')
        route('/overview/', 'views.overview.routed')
        route('/workflows/analyses/:analysisId', 'views.workflows.routedAnalysis')
        route(
            '/workflows/variants/:alleleReference/:alleleIdentifier',
            'views.workflows.routedAllele'
        )
        route('/dashboard', 'views.dashboard.routed')
        route('/login', 'views.login.routed')
        route('/*', 'views.defaultRouted')

        page.exit('/workflows/*', (ctx, next) => {
            const state = cerebral.controller.getState()
            if (checkUnsavedInterpretation(state)) {
                const ans = confirm(
                    'You have unsaved work. Are you sure you want to leave the page? Any unsaved changes will be lost.'
                )
                if (!ans) {
                    page.replace(ctx.path, ctx.state, null, false)
                }
            }
            next()
        })
        page.start()
    }
}
