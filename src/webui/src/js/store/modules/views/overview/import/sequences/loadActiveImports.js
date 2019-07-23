import { sequence } from 'cerebral'
import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import toast from '../../../../../common/factories/toast'
import getImportJobs from '../actions/getImportJobs'

export default sequence('loadActiveImports', [
    () => {
        return { page: 1, perPage: 999, q: { status: ['RUNNING', 'SUBMITTED'] } }
    },
    getImportJobs,
    {
        success: [set(state`views.overview.import.data.activeImportJobs`, props`result.entries`)],
        error: [toast('error', 'Failed to get active import jobs')]
    }
])
