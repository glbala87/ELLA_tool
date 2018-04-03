import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'

app.component('alleleInfoFrequencyIndb', {
    bindings: {
        allelePath: '<'
    },
    templateUrl: 'ngtmpl/alleleInfoFrequencyIndb.ngtmpl.html',
    controller: connect(
        {
            allele: state`${props`allelePath`}`
        },
        'AlleleInfoFrequencyIndb'
    )
})
