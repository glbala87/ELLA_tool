import addTranscripts from '../actions/addTranscripts'
import filterAndFlattenGenepanel from '../actions/filterAndFlattenGenepanel'

export default [
    addTranscripts,
    filterAndFlattenGenepanel(
        'views.overview.import.custom.added.addedGenepanel',
        'views.overview.import.custom.added.filteredFlattened',
        'views.overview.import.custom.added.filter'
    )
]
