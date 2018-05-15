import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import filterAndFlattenGenepanel from '../actions/filterAndFlattenGenepanel'

export default [
    set(state`views.overview.import.added.filter`, props`filter`),
    filterAndFlattenGenepanel(
        'views.overview.import.added.addedGenepanel',
        'views.overview.import.added.filteredFlattened',
        'views.overview.import.added.filter'
    ),
    set(state`views.overview.import.added.selectedPage`, 1)
]
