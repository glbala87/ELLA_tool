import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import getAttachments from '../actions/getAttachments'
import toastr from '../../../../common/factories/toastr'

export default [
    getAttachments,
    {
        success: [set(state`views.workflows.data.attachments`, props`result`)],
        error: [toastr('error', 'Failed to load attachments', 30000)]
    }
]
