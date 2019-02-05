/* jshint esnext: true */

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { signal } from 'cerebral/tags'
import template from './reassignWorkflow.ngtmpl.html'

app.component('reassignWorkflow', {
    templateUrl: 'reassignWorkflow.ngtmpl.html',
    controller: connect(
        {
            reassignWorkflowClicked: signal`views.workflows.modals.reassignWorkflow.reassignWorkflowClicked`,
            dismissClicked: signal`views.workflows.modals.reassignWorkflow.dismissClicked`
        },
        'ReassignWorkflow',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    close() {
                        $ctrl.dismissClicked()
                    },
                    reassign() {
                        $ctrl.reassignWorkflowClicked()
                    }
                })
            }
        ]
    )
})
