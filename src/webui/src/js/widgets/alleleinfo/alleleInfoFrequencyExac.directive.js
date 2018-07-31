import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'
import template from './alleleInfoFrequencyExac.ngtmpl.html'

app.component('alleleInfoFrequencyExac', {
    bindings: {
        allelePath: '<'
    },
    template,
    controller: connect(
        {
            allele: state`${props`allelePath`}`
        },
        'AlleleInfoFrequencyExac'
    )
})
