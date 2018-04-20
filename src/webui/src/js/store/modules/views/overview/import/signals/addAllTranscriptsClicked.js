import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import addTranscripts from '../actions/addTranscripts'
import filterGenepanel from '../actions/filterGenepanel'

export default [
    set(props`added`, state`views.overview.import.candidates.filteredFlattened`),
    addTranscripts,
    filterGenepanel(
        'views.overview.import.added.addedGenepanel',
        'views.overview.import.added.filteredGenepanel',
        'views.overview.import.added.filteredFlattened',
        'views.overview.import.added.filter'
    )
]
