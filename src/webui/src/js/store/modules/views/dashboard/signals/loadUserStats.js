import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getUserStats from '../actions/getUserStats'

export default [
    getUserStats,
    {
        success: [
            set(state`views.dashboard.data.userStats`, props`result`),
            set(state`views.dashboard.error`, false)
        ],
        error: [set(state`views.dashboard.error`, true)]
    }
]
