import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'

app.component('alleleInfoFrequencyExac', {
    bindings: {
        allelePath: '<'
    },
    templateUrl: 'ngtmpl/alleleInfoFrequencyExac.ngtmpl.html',
    controller: connect(
        {
            allele: state`${props`allelePath`}`
        },
        'AlleleInfoFrequencyExac'
    )
})
