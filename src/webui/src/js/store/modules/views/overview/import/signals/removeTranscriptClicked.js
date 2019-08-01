import removeTranscripts from '../actions/removeTranscripts'
import filterAndFlattenGenepanel from '../actions/filterAndFlattenGenepanel'

export default [
    removeTranscripts,
    filterAndFlattenGenepanel(
        'views.overview.import.custom.added.addedGenepanel',
        'views.overview.import.custom.added.filteredFlattened',
        'views.overview.import.custom.added.filter'
    )
]
