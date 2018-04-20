import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import filterGenepanel from '../actions/filterGenepanel'

export default [
    set(state`views.overview.import.added.filter`, props`filter`),
    filterGenepanel(
        'views.overview.import.added.addedGenepanel',
        'views.overview.import.added.filteredGenepanel',
        'views.overview.import.added.filteredFlattened',
        'views.overview.import.added.filter'
    ),
    set(state`views.overview.import.added.selectedPage`, 1)
]
