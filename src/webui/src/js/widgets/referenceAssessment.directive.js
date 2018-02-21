import { Directive } from '../ng-decorators'

/***
 * Display (some of) a reference assessment
 */

import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'
import getReferenceAssessment from '../store/modules/views/workflows/interpretation/computed/getReferenceAssessment'

app.component('referenceassessment', {
    bindings: {
        referenceId: '='
    },
    templateUrl: 'ngtmpl/referenceAssessment-new.ngtmpl.html',
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

@Directive({
    selector: 'referenceassessment-old',
    scope: {
        referenceassessment: '='
    },
    templateUrl: 'ngtmpl/referenceAssessment.ngtmpl.html'
})
export class ReferenceAssessment {}
