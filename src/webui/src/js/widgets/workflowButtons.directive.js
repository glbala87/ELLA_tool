import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { hasDataAtKey } from '../util'
import template from './workflowButtons.ngtmpl.html'
import getSelectedInterpretation from '../store/modules/views/workflows/computed/getSelectedInterpretation'

const START_BUTTON_OPTIONS = {
    save: 'Save',
    'Not ready': 'Start not ready',
    Interpretation: 'Start interpretation',
    Review: 'Start review',
    'Medical review': 'Start med. review',
    reopen: 'Reopen',
    override: 'Reassign to me'
}

app.component('workflowButtons', {
    bindings: {
        startWhenReopen: '=?'
    },
    templateUrl: 'workflowButtons.ngtmpl.html',
    controller: connect(
        {
            config: state`app.config`,
            type: state`views.workflows.type`,
            id: state`views.workflows.id`,
            startClicked: signal`views.workflows.startClicked`,
            showFinishConfirmationClicked: signal`views.workflows.modals.finishConfirmation.showFinishConfirmationClicked`,
            startMode: state`views.workflows.startMode`,
            selectedInterpretation: getSelectedInterpretation,
            dirty: state`views.workflows.interpretation.dirty`,
            user: state`app.user`
        },
        'WorkflowButtons',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    startClickedWrapper() {
                        $ctrl.startClicked({ startWhenReopen: $ctrl.startWhenReopen || false })
                    },
                    showStartBtn() {
                        const userConfig = $ctrl.config.user.user_config
                        return hasDataAtKey(userConfig, 'workflows', $ctrl.type, 'can_start')
                            ? Boolean(userConfig.workflows[$ctrl.type].can_start)
                            : true // default
                    },
                    getStartBtnText: () => {
                        if ($ctrl.startMode === 'reopen' && $ctrl.startWhenReopen) {
                            return START_BUTTON_OPTIONS[
                                $ctrl.selectedInterpretation.workflow_status
                            ]
                        }
                        return START_BUTTON_OPTIONS[$ctrl.startMode]
                    },
                    getStartBtnClass: () => {
                        let classes = []
                        if (
                            ['Not ready', 'Interpretation', 'Review', 'Medical review'].includes(
                                $ctrl.startMode
                            )
                        ) {
                            classes.push('green')
                        } else if (['override'].includes($ctrl.startMode)) {
                            classes.push('red')
                        } else {
                            if ($ctrl.dirty) {
                                classes.push('pink')
                            } else {
                                classes.push('blue')
                            }
                        }
                        return classes
                    },
                    showFinishBtn: () => {
                        if (
                            $ctrl.selectedInterpretation &&
                            $ctrl.selectedInterpretation.status === 'Ongoing'
                        ) {
                            return $ctrl.selectedInterpretation.user.id === $ctrl.user.id
                        }
                        return false
                    }
                })
            }
        ]
    )
})
