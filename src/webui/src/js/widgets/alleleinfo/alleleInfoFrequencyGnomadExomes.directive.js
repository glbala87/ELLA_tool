/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, string, signal } from 'cerebral/tags'

app.component('alleleInfoFrequencyGnomadExomes', {
    templateUrl: 'ngtmpl/alleleInfoFrequencyGnomadExomes-new.ngtmpl.html',
    controller: connect(
        {
            allele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`
        },
        'AlleleInfoFrequencyGnomadExomes'
    )
})

@Directive({
    selector: 'allele-info-frequency-gnomad-exomes-old',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoFrequencyGnomadExomes.ngtmpl.html'
})
@Inject()
export class AlleleInfoFrequencyGnomadExomes {
    constructor() {}

    hasContent() {
        return 'GNOMAD_EXOMES' in this.allele.annotation.frequencies
    }
}
