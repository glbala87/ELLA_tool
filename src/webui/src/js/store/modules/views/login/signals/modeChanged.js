import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'

export default [set(state`views.login.mode`, props`mode`)]
