/* jshint esnext: true */

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state } from 'cerebral/tags'

import template from './workflow.ngtmpl.html'

app.component('workflow', {
    templateUrl: 'workflow.ngtmpl.html',
    controller: connect(
        {
            loaded: state`views.workflows.loaded`
        },
        'Workflow'
    )
})
