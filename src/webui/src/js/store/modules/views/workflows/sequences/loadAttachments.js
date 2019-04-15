import { set } from 'cerebral/operators'
import { props, state } from 'cerebral/tags'
import toast from '../../../../common/factories/toast'
import getAttachments from '../actions/getAttachments'

export default [
    getAttachments,
    {
        success: [set(state`views.workflows.interpretation.data.attachments`, props`result`)],
        error: [toast('error', 'Failed to load attachments', 30000)]
    }
]
