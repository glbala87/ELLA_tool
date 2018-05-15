import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getAnalysesForAllele from '../actions/getAnalysesForAllele'
import toastr from '../../../common/factories/toastr'

export default [
    getAnalysesForAllele,
    {
        success: [set(state`modals.showAnalysesForAllele.data.analyses`, props`result`)],
        error: [toastr('error', 'An error occured while fetching analyses.')]
    }
]
