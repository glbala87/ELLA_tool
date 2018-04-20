import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import filterGenepanel from '../actions/filterGenepanel'

export default [
    set(state`views.overview.import.candidates.filter`, props`filter`),
    set(state`views.overview.import.candidates.selectedPage`, 1),
    filterGenepanel(
        'views.overview.import.data.genepanel',
        'views.overview.import.candidates.filteredGenepanel',
        'views.overview.import.candidates.filteredFlattened',
        'views.overview.import.candidates.filter'
    )
]
