/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

import isReadOnly from '../../store/modules/views/workflows/computed/isReadOnly'

app.component('alleleInfoClassification', {
    templateUrl: 'ngtmpl/alleleInfoClassification.ngtmpl.html',
    controller: connect(
        {
            allele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`,
            readOnly: isReadOnly,
            showAlleleAssessmentHistory: signal`views.workflows.interpretation.showAlleleAssessmentHistoryClicked`
        },
        'AlleleInfoClassification'
    )
})
