import { push } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import removeTranscripts from '../actions/removeTranscripts'
import filterGenepanel from '../actions/filterGenepanel'

export default [
    removeTranscripts,
    filterGenepanel(
        'views.overview.import.added.addedGenepanel',
        'views.overview.import.added.filteredGenepanel',
        'views.overview.import.added.filteredFlattened',
        'views.overview.import.added.filter'
    )
]
