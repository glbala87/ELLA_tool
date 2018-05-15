import { set, equals, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import checkConfirmPassword from '../actions/checkConfirmPassword'

export default [
    set(state`views.login.confirmNewPassword`, props`confirmNewPassword`),
    checkConfirmPassword
]
