import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getBroadcast from '../actions/getBroadcast'
import toast from '../factories/toast'

export default [
    getBroadcast,
    {
        success: [set(state`app.broadcast.messages`, props`result`)],
        error: [toast('error', 'Failed to load broadcast messages')]
    }
]
