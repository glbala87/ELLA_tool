/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'
import getWorseConsequenceTranscripts from '../../store/common/computes/getWorseConsequenceTranscripts'

app.component('alleleInfoConsequence', {
    bindings: {
        allelePath: '<'
    },
    templateUrl: 'ngtmpl/alleleInfoConsequence-new.ngtmpl.html',
    controller: connect(
        {
            allele: state`${props`allelePath`}`,
            worstConsequenceTranscripts: getWorseConsequenceTranscripts(state`${props`allelePath`}`)
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
