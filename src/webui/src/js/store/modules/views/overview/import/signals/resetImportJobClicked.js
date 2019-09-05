import patchImportJob from '../actions/patchImportJob'
import toast from '../../../../../common/factories/toast'
import loadImportJobs from '../sequences/loadImportJobs'

export default [
    ({}) => {
        return { payload: { status: 'SUBMITTED' } }
    },
    patchImportJob,
    {
        success: [loadImportJobs],
        error: [toast('error', 'Failed to get reset import job')]
    }
]
