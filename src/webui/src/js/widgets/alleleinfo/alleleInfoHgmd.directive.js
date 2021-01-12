import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props } from 'cerebral/tags'
import template from './alleleInfoHgmd.ngtmpl.html' // eslint-disable-line no-unused-vars

app.component('alleleInfoHgmd', {
    bindings: {
        allelePath: '<'
    },
    templateUrl: 'alleleInfoHgmd.ngtmpl.html',
    controller: connect(
        {
            allele: state`${props`allelePath`}`
        },
        'AlleleInfoHgmd'
    )
})
