import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props } from 'cerebral/tags'
import template from './alleleInfoFrequencyIndb.ngtmpl.html' // eslint-disable-line no-unused-vars

app.component('alleleInfoFrequencyIndb', {
    bindings: {
        allelePath: '<'
    },
    templateUrl: 'alleleInfoFrequencyIndb.ngtmpl.html',
    controller: connect(
        {
            allele: state`${props`allelePath`}`
        },
        'AlleleInfoFrequencyIndb'
    )
})