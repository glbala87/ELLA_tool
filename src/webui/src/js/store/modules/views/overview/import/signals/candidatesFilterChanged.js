import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import filterAndFlattenGenepanel from '../actions/filterAndFlattenGenepanel'

export default [
    set(state`views.overview.import.custom.candidates.filter`, props`filter`),
    set(state`views.overview.import.custom.candidates.selectedPage`, 1),
    filterAndFlattenGenepanel(
        'views.overview.import.data.genepanel',
        'views.overview.import.custom.candidates.filteredFlattened',
        'views.overview.import.custom.candidates.filter'
    )
]
