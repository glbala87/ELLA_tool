import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props } from 'cerebral/tags'
import getWorseConsequenceTranscripts from '../../store/common/computes/getWorseConsequenceTranscripts'
import template from './alleleInfoConsequence.ngtmpl.html'
import popover from './alleleInfoConsequencePopover.ngtmpl.html'

app.component('alleleInfoConsequence', {
    bindings: {
        allelePath: '<'
    },
    templateUrl: 'alleleInfoConsequence.ngtmpl.html',
    controller: connect(
        {
            allele: state`${props`allelePath`}`,
            worstConsequenceTranscripts: getWorseConsequenceTranscripts(state`${props`allelePath`}`)
        },
        'AlleleInfoConsequence'
    )
})
