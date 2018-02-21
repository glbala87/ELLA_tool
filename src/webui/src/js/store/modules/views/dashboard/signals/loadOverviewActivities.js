import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getOverviewActivities from '../actions/getOverviewActivities'

export default [
    set(state`views.dashboard.loading`, true),
    getOverviewActivities,
    {
        success: [
            set(state`views.dashboard.data.activities`, props`result`),
            set(state`views.dashboard.error`, false)
        ],
        error: [set(state`views.dashboard.error`, true)]
    },
    set(state`views.dashboard.loading`, false)
]
