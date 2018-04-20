import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'

export default [
    set(state`views.overview.import.added.addedGenepanel.genes`, {}),
    set(state`views.overview.import.added.filteredFlattened`, []),
    set(state`views.overview.import.added.selectedPage`, 1)
]
