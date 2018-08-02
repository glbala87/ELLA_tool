import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'
import getReferenceAssessment from '../store/modules/views/workflows/interpretation/computed/getReferenceAssessment'
import template from './referenceAssessment.ngtmpl.html'

app.component('referenceassessment', {
    bindings: {
        referenceId: '='
    },
    templateUrl: 'referenceAssessment.ngtmpl.html',
    controller: connect(
        {
            referenceAssessment: getReferenceAssessment(
                state`views.workflows.selectedAllele`,
                props`referenceId`
            )
        },
        'ReferenceAssessment'
    )
})
