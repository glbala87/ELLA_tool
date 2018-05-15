import addTranscripts from '../actions/addTranscripts'
import filterAndFlattenGenepanel from '../actions/filterAndFlattenGenepanel'

export default [
    addTranscripts,
    filterAndFlattenGenepanel(
        'views.overview.import.added.addedGenepanel',
        'views.overview.import.added.filteredFlattened',
        'views.overview.import.added.filter'
    )
]
