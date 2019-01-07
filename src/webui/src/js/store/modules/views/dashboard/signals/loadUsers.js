import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getAllUsers from '../../../../../store/common/actions/getAllUsers'
import toast from '../../../../common/factories/toast'

// Populate state with users belonging to the same group

function userByGroup({ props, state }) {
    const EMPTY_LIST = []
    console.log(props)
    return {
        // exclude current user
        usersInGroup: !props.result
            ? EMPTY_LIST
            : props.result.filter(
                  (u) =>
                      u.group.name === state.get('app.user.group.name') &&
                      u.id !== state.get('app.user.id')
              )
    }
}

export default [
    getAllUsers,
    {
        success: [userByGroup, set(state`views.dashboard.data.usersInGroup`, props`usersInGroup`)],
        error: [toast('error', 'Cannot find other users')]
    }
]
