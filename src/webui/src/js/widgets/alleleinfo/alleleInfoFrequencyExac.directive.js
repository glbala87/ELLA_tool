/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, string, signal } from 'cerebral/tags'

app.component('alleleInfoFrequencyExac', {
    templateUrl: 'ngtmpl/alleleInfoFrequencyExac-new.ngtmpl.html',
    controller: connect(
        {
            allele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`
        },
        'AlleleInfoFrequencyExac'
    )
})

@Directive({
    selector: 'allele-info-frequency-exac-old',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoFrequencyExac.ngtmpl.html'
})
@Inject()
export class AlleleInfoFrequencyExac {
    constructor() {}

    hasContent() {
        return 'ExAC' in this.allele.annotation.frequencies
    }
}
