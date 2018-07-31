import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'
import getWorseConsequenceTranscripts from '../../store/common/computes/getWorseConsequenceTranscripts'
import template from './alleleInfoConsequence.ngtmpl.html'

app.component('alleleInfoConsequence', {
    bindings: {
        allelePath: '<'
    },
    template,
    controller: connect(
        {
            allele: state`${props`allelePath`}`,
            worstConsequenceTranscripts: getWorseConsequenceTranscripts(state`${props`allelePath`}`)
        },
        'AlleleInfoConsequence'
    )
})
