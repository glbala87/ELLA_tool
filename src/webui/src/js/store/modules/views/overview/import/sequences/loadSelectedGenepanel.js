import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getGenepanel from '../actions/getGenepanel'
import toast from '../../../../../common/factories/toast'
import filterAndFlattenGenepanel from '../actions/filterAndFlattenGenepanel'

export default [
    set(props`genepanelName`, state`views.overview.import.selectedGenepanel.name`),
    set(props`genepanelVersion`, state`views.overview.import.selectedGenepanel.version`),
    getGenepanel,
    {
        success: [
            set(state`views.overview.import.data.genepanel`, props`result`),
            filterAndFlattenGenepanel(
                'views.overview.import.data.genepanel',
                'views.overview.import.custom.candidates.filteredFlattened',
                'views.overview.import.custom.candidates.filter'
            ),
            set(state`views.overview.import.custom.candidates.selectedPage`, 1)
        ],
        error: [toast('error', 'Failed to load genepanel')]
    }
]
