import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import postGenepanel from '../actions/postGenepanel'
import toast from '../../../../../common/factories/toast'
import postImportJob from '../actions/postImportJob'
import resetCustomImport from '../sequences/resetCustomImport'
import loadImportJobs from '../sequences/loadImportJobs'

export default [
    postImportJob,
    {
        success: [toast('success', 'Import created.'), loadImportJobs],
        error: [toast('error', 'Failed to submit imports')]
    }
]
