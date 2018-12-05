import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

import template from './overview.ngtmpl.html'

app.component('overview', {
    templateUrl: 'overview.ngtmpl.html',
    controller: connect(
        {
            sectionKeys: state`views.overview.sectionKeys`,
            sections: state`views.overview.sections`,
            loading: state`views.overview.loading`,
            sectionChanged: signal`views.overview.sectionChanged`
        },
        'Overview'
    )
})
