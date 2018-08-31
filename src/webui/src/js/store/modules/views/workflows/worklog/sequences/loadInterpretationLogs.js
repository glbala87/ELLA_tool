import { sequence } from 'cerebral'
import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getInterpretationLogs from '../actions/getInterpretationLogs'
import updateMessages from '../actions/updateMessages'
import toast from '../../../../../common/factories/toast'

export default sequence('loadInterpretationLogs', [
    getInterpretationLogs,
    {
        success: [
            set(state`views.workflows.data.interpretationlogs`, props`result`),
            updateMessages
        ],
        error: [toast('error', 'Failed to load work log')]
    }
])
