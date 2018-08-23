import app from '../ng-decorators'
import template from './interpretationRoundInfo.ngtmpl.html'

app.component('interpretationRoundInfo', {
    templateUrl: 'interpretationRoundInfo.ngtmpl.html',
    bindings: {
        index: '@',
        interpretation: '<'
    },
    controller: [
        '$scope',
        ($scope) => {
            const $ctrl = $scope.$ctrl

            Object.assign($ctrl, {
                getEndAction: () => {
                    let end_action = `${$ctrl.interpretation.workflow_status} ${
                        $ctrl.interpretation.finalized ? ' (Finalized) ' : ' '
                    }`
                    if ($ctrl.interpretation.user) {
                        return end_action + ' • '
                    } else {
                        return end_action
                    }
                }
            })
        }
    ]
})
