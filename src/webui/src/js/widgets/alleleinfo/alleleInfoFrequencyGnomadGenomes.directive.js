import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'

app.component('alleleInfoFrequencyGnomadGenomes', {
    bindings: {
        allelePath: '<'
    },
    templateUrl: 'ngtmpl/alleleInfoFrequencyGnomadGenomes.ngtmpl.html',
    controller: connect(
        {
            allele: state`${props`allelePath`}`
        },
        'AlleleInfoFrequencyGnomadGenomes'
    )
})
