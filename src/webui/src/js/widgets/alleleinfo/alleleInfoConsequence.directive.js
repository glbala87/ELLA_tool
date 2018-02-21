/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import getWorseConsequenceTranscripts from '../../store/common/computes/getWorseConsequenceTranscripts'

app.component('alleleInfoConsequence', {
    templateUrl: 'ngtmpl/alleleInfoConsequence-new.ngtmpl.html',
    controller: connect(
        {
            allele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`,
            worstConsequenceTranscripts: getWorseConsequenceTranscripts(
                state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`
            )
        },
        'AlleleInfoConsequence'
    )
})

@Directive({
    selector: 'allele-info-consequence-old',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoConsequence.ngtmpl.html'
})
@Inject()
export class AlleleInfoVariantConsequence {
    constructor() {}
}
