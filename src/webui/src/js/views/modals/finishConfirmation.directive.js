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
            isSubmitting: state`views.workflows.modals.finishConfirmation.submitting`,
            finishClicked: signal`views.workflows.modals.finishConfirmation.finishConfirmationClicked`,
            dismissClicked: signal`views.workflows.modals.finishConfirmation.dismissClicked`
        },
        'FinishConfirmation',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    close() {
                        $ctrl.dismissClicked()
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
                    },
                    finishDisabled() {
                        return (
                            ($ctrl.getSelectedStatus() == 'Finalized' &&
                                !$ctrl.canFinalize.canFinalize) ||
                            $ctrl.isSubmitting
                        )
                    },
                    finishButtonText() {
                        return $ctrl.isSubmitting ? 'Please wait' : 'Finish'
                    }
                })
            }
        ]
    )
})
