import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'
import getWorseConsequenceTranscripts from '../../store/common/computes/getWorseConsequenceTranscripts'

app.component('alleleInfoConsequence', {
    bindings: {
        allelePath: '<'
    },
    templateUrl: 'ngtmpl/alleleInfoConsequence.ngtmpl.html',
    controller: connect(
        {
            allele: state`${props`allelePath`}`,
            worstConsequenceTranscripts: getWorseConsequenceTranscripts(state`${props`allelePath`}`)
        },
        'AlleleInfoConsequence'
    )
})
