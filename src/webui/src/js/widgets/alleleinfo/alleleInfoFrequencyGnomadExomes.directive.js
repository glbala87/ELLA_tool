import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props } from 'cerebral/tags'
import template from './alleleInfoFrequencyGnomadExomes.ngtmpl.html'

app.component('alleleInfoFrequencyGnomadExomes', {
    bindings: {
        allelePath: '<'
    },
    templateUrl: 'alleleInfoFrequencyGnomadExomes.ngtmpl.html',
    controller: connect(
        {
            allele: state`${props`allelePath`}`
        },
        'AlleleInfoFrequencyGnomadExomes'
    )
})
