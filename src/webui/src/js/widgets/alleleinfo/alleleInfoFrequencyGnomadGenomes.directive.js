/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'

app.component('alleleInfoFrequencyGnomadGenomes', {
    bindings: {
        allelePath: '<'
    },
    templateUrl: 'ngtmpl/alleleInfoFrequencyGnomadGenomes-new.ngtmpl.html',
    controller: connect(
        {
            allele: state`${props`allelePath`}`
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
