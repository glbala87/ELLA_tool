/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'

app.component('alleleInfoFrequencyGnomadExomes', {
    bindings: {
        allelePath: '<'
    },
    templateUrl: 'ngtmpl/alleleInfoFrequencyGnomadExomes-new.ngtmpl.html',
    controller: connect(
        {
            allele: state`${props`allelePath`}`
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
