import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import toast from '../../../../../common/factories/toast'
import getSamples from '../actions/getSamples'

export default [
    getSamples,
    {
        success: [set(state`views.overview.import.data.samples`, props`result`)],
        error: [toast('error', 'Failed to search for samples')]
    }
]
