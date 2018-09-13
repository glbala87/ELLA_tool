import { when } from 'cerebral/operators'
import { props } from 'cerebral/tags'
import toast from '../../../../../common/factories/toast'
import loadInterpretationLogs from '../sequences/loadInterpretationLogs'
import deleteInterpretationLog from '../actions/deleteInterpretationLog'

export default [
    when(props`id`),
    {
        true: [
            deleteInterpretationLog,
            {
                success: [loadInterpretationLogs],
                error: [toast('error', 'Failed to delete message')]
            }
        ],
        false: []
    }
]
