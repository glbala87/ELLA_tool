import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import canFinalize from '../../store/modules/views/workflows/computed/canFinalize'
import template from './finishConfirmation.ngtmpl.html'
import getSelectedInterpretation from '../../store/modules/views/workflows/computed/getSelectedInterpretation'

app.component('finishConfirmation', {
    templateUrl: 'finishConfirmation.ngtmpl.html',
    controller: connect(
        {
            selectedInterpretation: getSelectedInterpretation,
            type: state`views.workflows.type`,
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
                    },
                    getSelectedStatus() {
                        if (!$ctrl.selectedStatus) {
                            $ctrl.selectedStatus = $ctrl.getWorkflowStatus()
                        }
                        return $ctrl.selectedStatus
                    },
                    getWorkflowStatus() {
                        return $ctrl.selectedInterpretation.workflow_status
                    },
                    selectStatus(status) {
                        $ctrl.selectedStatus = status
                    },
                    getClass(status) {
                        return status === $ctrl.selectedStatus ? 'blue' : 'normal'
                    }
                })
            }
        ]
    )
})
