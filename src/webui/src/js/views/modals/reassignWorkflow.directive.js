/* jshint esnext: true */

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { signal } from 'cerebral/tags'
import template from './reassignWorkflow.ngtmpl.html'

app.component('reassignWorkflow', {
    templateUrl: 'reassignWorkflow.ngtmpl.html',
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
