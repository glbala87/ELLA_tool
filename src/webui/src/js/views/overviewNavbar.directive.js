import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

import template from './overviewNavbar.ngtmpl.html'

app.component('overviewNavbar', {
    templateUrl: 'overviewNavbar.ngtmpl.html',
    controller: connect(
        {
            showVariantReport: state`app.config.user.user_config.overview.show_variant_report`,
            importJobsStatus: state`views.overview.importJobsStatus`,
            showImportModal: signal`views.overview.showImportModalClicked`
        },
        'OverviewNavbar'
    )
})
