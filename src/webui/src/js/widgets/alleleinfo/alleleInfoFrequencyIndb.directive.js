/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'

app.component('alleleInfoFrequencyIndb', {
    bindings: {
        allelePath: '<'
    },
    templateUrl: 'ngtmpl/alleleInfoFrequencyIndb-new.ngtmpl.html',
    controller: connect(
        {
            allele: state`${props`allelePath`}`
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
