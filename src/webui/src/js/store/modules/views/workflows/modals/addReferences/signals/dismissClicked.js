import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'

export default [set(state`views.workflows.modals.addReferences`, { show: false })]
