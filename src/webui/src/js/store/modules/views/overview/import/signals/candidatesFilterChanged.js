import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import filterAndFlattenGenepanel from '../actions/filterAndFlattenGenepanel'

export default [
    set(state`views.overview.import.candidates.filter`, props`filter`),
    set(state`views.overview.import.candidates.selectedPage`, 1),
    filterAndFlattenGenepanel(
        'views.overview.import.data.genepanel',
        'views.overview.import.candidates.filteredFlattened',
        'views.overview.import.candidates.filter'
    )
]
