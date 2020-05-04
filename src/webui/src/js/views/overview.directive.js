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
            selectedSection: state`views.overview.state.selectedSection`,
            loading: state`views.overview.loading`
        },
        'Overview',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl
                Object.assign($ctrl, {
                    isSelected: (section) => section === $ctrl.selectedSection
                })
            }
        ]
    )
})
