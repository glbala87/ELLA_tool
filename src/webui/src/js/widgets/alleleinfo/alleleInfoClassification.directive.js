/* jshint esnext: true */

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

import isReadOnly from '../../store/modules/views/workflows/computed/isReadOnly'
import template from './alleleInfoClassification.ngtmpl.html'

app.component('alleleInfoClassification', {
    templateUrl: 'alleleInfoClassification.ngtmpl.html',
    controller: connect(
        {
            allele: state`views.workflows.interpretation.data.alleles.${state`views.workflows.selectedAllele`}`,
            readOnly: isReadOnly,
            showAlleleAssessmentHistoryClicked: signal`views.workflows.modals.alleleAssessmentHistory.showAlleleAssessmentHistoryClicked`
        },
        'AlleleInfoClassification'
    )
})
