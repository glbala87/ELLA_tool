import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getUserStats from '../actions/getUserStats'
import toastr from "../../../../common/factories/toastr";

export default [
    getUserStats,
    {
        success: [set(state`views.dashboard.data.userStats`, props`result`)],
        error: [toastr('error', 'Failed finding user\'s work statistics')]
    }
]
