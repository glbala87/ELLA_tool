import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

import template from './overviewNavbar.ngtmpl.html'

app.component('overviewNavbar', {
    templateUrl: 'overviewNavbar.ngtmpl.html',
    controller: connect(
        {
            overviewFilter: state`views.overview.filter`,
            technologyHTS: state`views.overview.filter.technology.HTS`,
            technologySanger: state`views.overview.filter.technology.Sanger`,
            priorityNormal: state`views.overview.filter.priority.normal`,
            priorityHigh: state`views.overview.filter.priority.high`,
            priorityUrget: state`views.overview.filter.priority.urgent`,
            updateFilter: signal`views.overview.updateFilter`,
            clearFilter: signal`views.overview.clearFilter`
        },
        'OverviewNavbar'[
            ('$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl
                Object.assign($ctrl, {})
            })
        ]
    )
})
