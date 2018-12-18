import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props } from 'cerebral/tags'
import template from './alleleInfoFrequencyGnomadGenomes.ngtmpl.html'

app.component('alleleInfoFrequencyGnomadGenomes', {
    bindings: {
        allelePath: '<'
    },
    templateUrl: 'alleleInfoFrequencyGnomadGenomes.ngtmpl.html',
    controller: connect(
        {
            allele: state`${props`allelePath`}`
        },
        'AlleleInfoFrequencyGnomadGenomes'
    )
})
