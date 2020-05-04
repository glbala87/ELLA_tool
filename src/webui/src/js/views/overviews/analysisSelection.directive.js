import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import template from './analysisSelection.ngtmpl.html'

app.component('analysisSelection', {
    templateUrl: 'analysisSelection.ngtmpl.html',
    controller: connect(
        {
            analyses: state`views.overview.data.analyses`,
            finalized: state`views.overview.data.analysesFinalized`,
            state: state`views.overview.state.${state`views.overview.state.selectedSection`}`,
            selectedSection: state`views.overview.state.selectedSection`,
            finalizedPageChanged: signal`views.overview.finalizedPageChanged`,
            collapseChanged: signal`views.overview.collapseChanged`
        },
        'AnalysisSelection',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl
                Object.assign($ctrl, {
                    collapseChangedWrapper(collapsed, name) {
                        $ctrl.collapseChanged({
                            section: $ctrl.selectedSection,
                            name,
                            collapsed
                        })
                    }
                })
            }
        ]
    )
})
