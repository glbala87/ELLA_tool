import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import checkPasswordStrength from '../actions/checkPasswordStrength'

export default [set(state`views.login.newPassword`, props`newPassword`), checkPasswordStrength]
