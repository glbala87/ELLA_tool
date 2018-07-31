import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'
import template from './alleleInfoFrequencyIndb.ngtmpl.html'

app.component('alleleInfoFrequencyIndb', {
    bindings: {
        allelePath: '<'
    },
    template,
    controller: connect(
        {
            allele: state`${props`allelePath`}`
        },
        'AlleleInfoFrequencyIndb'
    )
})
