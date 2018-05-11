import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import selectedSection from '../../store/modules/views/overview/computed/selectedSection'

app.component('analysisSelection', {
    templateUrl: 'ngtmpl/analysisSelection.ngtmpl.html',
    controller: connect(
        {
            analyses: state`views.overview.data.analyses`,
            finalized: state`views.overview.data.analysesFinalized`,
            state: state`views.overview.state.${selectedSection}`,
            selectedSection: selectedSection,
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
