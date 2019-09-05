import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import filterAndFlattenGenepanel from '../actions/filterAndFlattenGenepanel'

export default [
    set(state`views.overview.import.custom.added.filter`, props`filter`),
    filterAndFlattenGenepanel(
        'views.overview.import.custom.added.addedGenepanel',
        'views.overview.import.custom.added.filteredFlattened',
        'views.overview.import.custom.added.filter'
    ),
    set(state`views.overview.import.custom.added.selectedPage`, 1)
]
