import { set } from 'cerebral/operators'
import { state } from 'cerebral/tags'

export default [
    set(state`views.overview.import.custom.added.addedGenepanel.genes`, {}),
    set(state`views.overview.import.custom.added.filteredFlattened`, []),
    set(state`views.overview.import.custom.added.selectedPage`, 1)
]
