import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state } from 'cerebral/tags'

import template from './workflowInterpretationRounds.ngtmpl.html'

app.component('workflowInterpretationRounds', {
    templateUrl: 'workflowInterpretationRounds.ngtmpl.html',
    controller: connect(
        {
            interpretations: state`views.workflows.data.interpretations`
        },
        'WorkflowInterpretationRounds',
        [
            '$scope',
            ($scope) => {
                $scope.$ctrl.test = function() {
                    console.log($ctrl.interpretations)
                }
            }
        ]
    )
})
