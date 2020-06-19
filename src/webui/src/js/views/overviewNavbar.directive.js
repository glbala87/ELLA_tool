import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

import template from './overviewNavbar.ngtmpl.html'
app.component('overviewNavbar', {
    templateUrl: 'overviewNavbar.ngtmpl.html',
    controller: connect(
        {
            overviewFilter: state`views.overview.filter`,
            filterApplied: state`views.overview.filterApplied`,
            technologyHTS: state`views.overview.filter.technologyHTS`,
            technologySanger: state`views.overview.filter.technologySanger`,
            priorityNormal: state`views.overview.filter.priorityNormal`,
            priorityHigh: state`views.overview.filter.priorityHigh`,
            priorityUrgent: state`views.overview.filter.priorityUrgent`,
            updateFilter: signal`views.overview.updateFilter`,
            clearFilter: signal`views.overview.clearFilter`
        },
        'OverviewNavbar'
    )
})
