import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getAnalysesForAllele from '../actions/getAnalysesForAllele'
import toast from '../../../../../common/factories/toast'

export default [
    set(state`search.modals.showAnalysesForAllele.warningAccepted`, true),
    getAnalysesForAllele,
    {
        success: [set(state`search.modals.showAnalysesForAllele.data.analyses`, props`result`)],
        error: [toast('error', 'An error occured while fetching analyses.')]
    }
]
