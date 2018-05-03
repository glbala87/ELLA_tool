import { set, get } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getAllUsers from '../../../../../store/common/actions/getAllUsers'

// Populate state with others the users belonging to the same group

function userByGroup({props, state })
{
    return {
        usersInGroup: props.result.filter( (u) =>
            u.group.name === state.get('app.user.group.name')
            && u.id !== state.get('app.user.id'))
    }
}

export default [
    getAllUsers,
    {
        success: [set(state`views.dashboard.error`, false)],
        error: [set(state`views.dashboard.error`, true)]
    },
    userByGroup,
    set(state`views.dashboard.data.usersInGroup`, props`usersInGroup`)

]