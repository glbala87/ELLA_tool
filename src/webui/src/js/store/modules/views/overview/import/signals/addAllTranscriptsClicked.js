import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import addTranscripts from '../actions/addTranscripts'
import filterAndFlattenGenepanel from '../actions/filterAndFlattenGenepanel'

export default [
    set(props`added`, state`views.overview.import.candidates.filteredFlattened`),
    addTranscripts,
    filterAndFlattenGenepanel(
        'views.overview.import.added.addedGenepanel',
        'views.overview.import.added.filteredFlattened',
        'views.overview.import.added.filter'
    )
]
