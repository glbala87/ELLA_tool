/* jshint esnext: true */

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state } from 'cerebral/tags'

import template from './workflowLoading.ngtmpl.html'

app.component('workflowLoading', {
    templateUrl: 'workflowLoading.ngtmpl.html',
    controller: connect(
        {
            loadingText: state`views.workflows.loadingText`
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
