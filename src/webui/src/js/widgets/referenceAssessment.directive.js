import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'
import getReferenceAssessment from '../store/modules/views/workflows/interpretation/computed/getReferenceAssessment'
import isReadOnly from '../store/modules/views/workflows/computed/isReadOnly'
import isAlleleAssessmentReused from '../store/modules/views/workflows/interpretation/computed/isAlleleAssessmentReused'
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
            ),
            isAlleleAssessmentReused: isAlleleAssessmentReused(
                state`views.workflows.selectedAllele`
            ),
            readOnly: isReadOnly,
            selectedAllele: state`views.workflows.selectedAllele`,
            referenceAssessmentCommentChanged: signal`views.workflows.interpretation.referenceAssessmentCommentChanged`
        },
        'ReferenceAssessment'
    )
})
