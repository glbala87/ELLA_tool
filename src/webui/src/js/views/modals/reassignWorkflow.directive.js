/* jshint esnext: true */

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

app.component('reassignWorkflow', {
    templateUrl: 'ngtmpl/reassignWorkflow.ngtmpl.html',
    controller: connect(
        {
            reassignWorkflowClicked: signal`views.workflows.reassignWorkflowClicked`,
            closeClicked: signal`closeModal`
        },
        'ReassignWorkflow',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    close() {
                        $ctrl.closeClicked({ modalName: 'reassignWorkflow' })
                    },
                    reassign() {
                        $ctrl.reassignWorkflowClicked()
                        $ctrl.close()
                    }
                })
            }
        ]
    )
})
