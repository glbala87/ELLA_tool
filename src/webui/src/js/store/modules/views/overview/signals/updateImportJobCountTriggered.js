import { parallel } from 'cerebral'
import { set } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import getImportJobs from '../actions/getImportJobs'
import toast from '../../../../common/factories/toast'

export default parallel([
    [
        () => {
            return { page: 1, perPage: 1, q: { status: ['RUNNING', 'SUBMITTED'] } }
        },
        getImportJobs,
        {
            success: [
                set(
                    state`views.overview.importJobsStatus.running`,
                    props`result.pagination.totalCount`
                )
            ],
            error: [toast('error', 'Failed to get import jobs status', 1000)]
        }
    ],
    [
        () => {
            return { page: 1, perPage: 1, q: { status: { $like: 'FAILED%' } } }
        },
        getImportJobs,
        {
            success: [
                set(
                    state`views.overview.importJobsStatus.failed`,
                    props`result.pagination.totalCount`
                )
            ],
            error: [toast('error', 'Failed to get import jobs status', 1000)]
        }
    ]
])
