import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import getAttachments from '../actions/getAttachments'
import toast from '../../../../common/factories/toast'

export default [
    getAttachments,
    {
        success: [set(state`views.workflows.data.attachments`, props`result`)],
        error: [toast('error', 'Failed to load attachments', 30000)]
    }
]
