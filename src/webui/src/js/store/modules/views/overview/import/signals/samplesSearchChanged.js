import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import toastr from '../../../../../common/factories/toastr'
import getSamples from '../actions/getSamples'

export default [
    getSamples,
    {
        success: [set(state`views.overview.import.data.samples`, props`result`)],
        error: [toastr('error', 'Failed to search for samples')]
    }
]
