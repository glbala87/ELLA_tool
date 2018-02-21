/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, string, signal } from 'cerebral/tags'

app.component('alleleInfoFrequencyGnomadGenomes', {
    templateUrl: 'ngtmpl/alleleInfoFrequencyGnomadGenomes-new.ngtmpl.html',
    controller: connect(
        {
            allele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`
        },
        'AlleleInfoFrequencyGnomadGenomes'
    )
})

@Directive({
    selector: 'allele-info-frequency-gnomad-genomes-old',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoFrequencyGnomadGenomes.ngtmpl.html'
})
@Inject()
export class AlleleInfoFrequencyGnomadGenomes {
    constructor() {}

    hasContent() {
        return 'GNOMAD_GENOMES' in this.allele.annotation.frequencies
    }
}
