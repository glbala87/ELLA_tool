import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import updateMessages from '../actions/updateMessages'

export default [
    set(state`views.workflows.worklog.showMessagesOnly`, props`showMessagesOnly`),
    updateMessages
]
