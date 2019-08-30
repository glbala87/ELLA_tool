import { sequence } from 'cerebral'
import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import toast from '../../../../../common/factories/toast'
import getImportJobs from '../actions/getImportJobs'

export default sequence('loadImportHistory', [
    ({ state }) => {
        const page = state.get('views.overview.import.importHistoryPage')
        return {
            page: page,
            perPage: 10,
            q: {
                status: [
                    'CANCELLED',
                    'DONE',
                    'FAILED (SUBMISSION)',
                    'FAILED (ANNOTATION)',
                    'FAILED (DEPOSIT)',
                    'FAILED (PROCESSING)'
                ]
            }
        }
    },
    getImportJobs,
    {
        success: [set(state`views.overview.import.data.importJobsHistory`, props`result`)],
        error: [toast('error', 'Failed to get import history')]
    }
])
