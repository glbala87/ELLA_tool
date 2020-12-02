import { state, props } from 'cerebral/tags'
import { set } from 'cerebral/operators'

export default [
    set(state`views.workflows.alleleSidebar.callerTypeSelected`, props`callerTypeSelected`)
]
