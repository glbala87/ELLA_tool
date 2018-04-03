import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import canFinalize from '../store/modules/views/workflows/computed/canFinalize'

app.component('finishConfirmation', {
    templateUrl: 'ngtmpl/finishConfirmation.ngtmpl.html',
    controller: connect(
        {
            canFinalize,
            finishClicked: signal`views.workflows.finishConfirmationClicked`,
            closeClicked: signal`closeModal`
        },
        'FinishConfirmation',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    close() {
                        $ctrl.closeClicked({ modalName: 'finishConfirmation' })
                    }
                })
            }
        ]
    )
})
