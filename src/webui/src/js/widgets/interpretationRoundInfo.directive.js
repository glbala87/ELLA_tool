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
                    let end_action = $ctrl.interpretation.workflow_status
                    if ($ctrl.interpretation.finalized) {
                        end_action += ' (Finalized) '
                    } else if ($ctrl.interpretation.status === 'Ongoing') {
                        end_action += ' (Ongoing) '
                    } else {
                        end_action += ' '
                    }

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
