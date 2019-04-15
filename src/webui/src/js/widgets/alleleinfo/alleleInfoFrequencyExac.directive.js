import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props } from 'cerebral/tags'
import template from './alleleInfoFrequencyExac.ngtmpl.html'

app.component('alleleInfoFrequencyExac', {
    bindings: {
        allelePath: '<'
    },
    templateUrl: 'alleleInfoFrequencyExac.ngtmpl.html',
    controller: connect(
        {
            allele: state`${props`allelePath`}`
        },
        'AlleleInfoFrequencyExac'
    )
})
