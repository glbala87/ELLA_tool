import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'

export default [
    set(state`views.workflows.modals.addExternal.selection.${props`key`}`, props`value`)
]
