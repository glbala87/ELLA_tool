import page from 'page'
import qs from 'query-string'
import { Inject, Run } from '../../ng-decorators'

// This is all spaghetti code due to how the CerebralJS <-> AngularJS integration is setup
// We don't have access to the Cerebral controller object upon initialization, as it's created
// inside the CerebralJS AngularJS binding module.
// The following is confusingly run _after_ all of the code above is run, after Cerebral is fully
// configured by AngularJS (see the main index.js).
class RouterInit {
    @Run()
    @Inject('cerebral')
    init(cerebral) {
        function route(url, signalPath) {
            page(url, ({ path, params, querystring }) => {
                const query = qs.parse(querystring)
                console.log(signalPath, Object.assign({}, params, query))
                cerebral.controller.getSignal(signalPath)(Object.assign({}, params, query))
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
        page.start()
    }
}
