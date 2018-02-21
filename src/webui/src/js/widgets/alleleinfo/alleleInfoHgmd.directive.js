/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

app.component('alleleInfoHgmd', {
    templateUrl: 'ngtmpl/alleleInfoHgmd-new.ngtmpl.html',
    controller: connect(
        {
            allele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`
        },
        'AlleleInfoHgmd'
    )
})

@Directive({
    selector: 'allele-info-hgmd-old',
    scope: {
        allele: '='
    },
    templateUrl: 'ngtmpl/alleleInfoHgmd.ngtmpl.html'
})
@Inject()
export class AlleleInfoHgmd {
    constructor() {
        if (!this.hasContent()) {
            this.collapsed = true
        }
    }

    hasContent() {
        return 'HGMD' in this.allele.annotation.external
    }
}
