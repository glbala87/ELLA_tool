import postInterpretationLog from '../actions/postInterpretationLog'
import createInterpretationLog from '../actions/createInterpretationLog'
import toast from '../../../../../common/factories/toast'
import loadInterpretationLogs from '../sequences/loadInterpretationLogs'

export default [
    createInterpretationLog,
    postInterpretationLog,
    {
        success: [loadInterpretationLogs],
        error: [toast('error', 'Failed to update overview comment')]
    }
]
