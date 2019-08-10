import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'

export default [
    set(state`views.workflows.modals.genepanelOverview.geneFilter`, props`filter`),
    set(state`views.workflows.modals.genepanelOverview.filteredGenesPage`, 1)
]
