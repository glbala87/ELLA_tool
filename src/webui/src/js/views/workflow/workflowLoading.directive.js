/* jshint esnext: true */

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state } from 'cerebral/tags'

import template from './workflowLoading.ngtmpl.html'

app.component('workflowLoading', {
    templateUrl: 'workflowLoading.ngtmpl.html',
    controller: connect(
        {
            loadingWorkflow: state`views.workflows.loadingWorkflow`
        },
        'WorkflowLoading',
        [
            '$scope',
            function($scope) {
                Object.assign($scope.$ctrl, {})
            }
        ]
    )
})
