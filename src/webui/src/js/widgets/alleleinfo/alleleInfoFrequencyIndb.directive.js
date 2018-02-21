/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, string, signal } from 'cerebral/tags'

app.component('alleleInfoFrequencyIndb', {
    templateUrl: 'ngtmpl/alleleInfoFrequencyIndb-new.ngtmpl.html',
    controller: connect(
        {
            allele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`
        },
        'AlleleInfoFrequencyIndb'
    )
})

@Directive({
    selector: 'allele-info-frequency-indb-old',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoFrequencyIndb.ngtmpl.html'
})
@Inject()
export class AlleleInfoFrequencyIndb {
    constructor() {
        if (!this.hasContent()) {
            this.collapsed = true
        }
    }

    hasContent() {
        return 'inDB' in this.allele.annotation.frequencies
    }
}
