import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getUserStats from '../actions/getUserStats'
import toast from '../../../../common/factories/toast'

export default [
    getUserStats,
    {
        success: [set(state`views.dashboard.data.userStats`, props`result`)],
        error: [toast('error', "Failed finding user's work statistics")]
    }
]
