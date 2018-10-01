import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import postInterpretationLog from '../actions/postInterpretationLog'
import createInterpretationLog from '../actions/createInterpretationLog'
import toast from '../../../../../common/factories/toast'
import loadInterpretationLogs from '../sequences/loadInterpretationLogs'

export default [
    when(props`message`),
    {
        true: [
            createInterpretationLog,
            postInterpretationLog,
            {
                success: [set(state`views.workflows.worklog.message`, ''), loadInterpretationLogs],
                error: [toast('error', 'Failed to add message')]
            }
        ],
        false: []
    }
]
