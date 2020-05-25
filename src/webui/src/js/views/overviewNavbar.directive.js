import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

import template from './overviewNavbar.ngtmpl.html'

app.component('overviewNavbar', {
    templateUrl: 'overviewNavbar.ngtmpl.html',
    controller: connect(
        {
            overviewFilter: state`views.overview.filter`,
            updateFilter: signal`views.overview.updateFilter`,
            clearFilter: signal`views.overview.clearFilter`
        },
        'OverviewNavbar'
        // [
        //     '$scope',
        //     ($scope) => {
        //         const $ctrl = $scope.$ctrl
        //         Object.assign($ctrl, {
        //             overviewFilterWrapper(collapsed, name) {
        //                 $ctrl.overviewFilter({
        //                     section: $ctrl.selectedSection,
        //                     name,
        //                     collapsed
        //                 })
        //             }
        //         })
        //     }
        // ]
    )
})
