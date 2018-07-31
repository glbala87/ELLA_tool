/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

import isReadOnly from '../../store/modules/views/workflows/computed/isReadOnly'
import template from './alleleInfoClassification.ngtmpl.html'

app.component('alleleInfoClassification', {
    template,
    controller: connect(
        {
            allele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`,
            readOnly: isReadOnly,
            showAlleleAssessmentHistory: signal`views.workflows.interpretation.showAlleleAssessmentHistoryClicked`
        },
        'AlleleInfoClassification'
    )
})
