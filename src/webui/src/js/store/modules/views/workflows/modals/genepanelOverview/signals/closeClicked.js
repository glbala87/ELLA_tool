import { set } from 'cerebral/operators'
import { state } from 'cerebral/tags'

export default [
    set(state`views.workflows.modals.genepanelOverview`, {
        show: false
    })
]
