import { when } from 'cerebral/operators'
import { props } from 'cerebral/tags'
import toast from '../../../../../common/factories/toast'
import loadInterpretationLogs from '../sequences/loadInterpretationLogs'
import patchInterpretationLog from '../actions/patchInterpretationLog'

export default [
    when(props`interpretationLog`),
    {
        true: [
            patchInterpretationLog,
            {
                success: [loadInterpretationLogs],
                error: [toast('error', 'Failed to edit message')]
            }
        ],
        false: []
    }
]
