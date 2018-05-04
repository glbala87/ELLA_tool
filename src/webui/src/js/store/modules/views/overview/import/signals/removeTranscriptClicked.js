import { push } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import removeTranscripts from '../actions/removeTranscripts'
import filterAndFlattenGenepanel from '../actions/filterAndFlattenGenepanel'

export default [
    removeTranscripts,
    filterAndFlattenGenepanel(
        'views.overview.import.added.addedGenepanel',
        'views.overview.import.added.filteredFlattened',
        'views.overview.import.added.filter'
    )
]
