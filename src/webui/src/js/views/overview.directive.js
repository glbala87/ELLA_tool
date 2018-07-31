import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

import template from './overview.ngtmpl.html'

app.component('overview', {
    template,
    controller: connect(
        {
            importJobsStatus: state`views.overview.importJobsStatus`,
            sectionKeys: state`views.overview.sectionKeys`,
            sections: state`views.overview.sections`,
            loading: state`views.overview.loading`,
            sectionChanged: signal`views.overview.sectionChanged`,
            showImportModal: signal`views.overview.showImportModalClicked`
        },
        'Overview'
    )
})
