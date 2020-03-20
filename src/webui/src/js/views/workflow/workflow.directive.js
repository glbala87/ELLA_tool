/* jshint esnext: true */

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state } from 'cerebral/tags'
import shouldShowSidebar from '../../store/modules/views/workflows/alleleSidebar/computed/shouldShowSidebar'

import template from './workflow.ngtmpl.html'

app.component('workflow', {
    templateUrl: 'workflow.ngtmpl.html',
    controller: connect(
        {
            loaded: state`views.workflows.loaded`,
            showSidebar: shouldShowSidebar
        },
        'Workflow'
    )
})
